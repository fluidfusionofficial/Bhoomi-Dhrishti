"""
Parcel profile endpoint with tiered disclosure.

Disclosure tiers:
  PUBLIC           — no auth, geometry + ULPIN + encumbered/dispute booleans
  CITIZEN_OWN      — authenticated citizen viewing their own parcel
  CONSENT_GATED    — citizen viewing another's parcel with consent
  OFFICER          — revenue/field officer, full detail
  ADMIN/COLLECTOR  — everything
"""
from __future__ import annotations

import asyncio
import json
import uuid
from typing import Optional

import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.schemas.parcel import (
    PublicParcelProfile,
    CitizenOwnParcelProfile,
    OfficerParcelProfile,
    RightEntry,
    EncumbranceEntry,
    DisputeEntry,
    DeedEntry,
    ConflictEntry,
)

logger = structlog.get_logger()
router = APIRouter()

OFFICER_ROLES = {"REVENUE_OFFICER", "FIELD_OFFICER", "REGISTRATION_OFFICER"}
ADMIN_ROLES = {"DISTRICT_COLLECTOR", "STATE_ADMIN", "SYSTEM_ADMIN"}


def _parse_role(authorization: Optional[str]) -> tuple[str, Optional[str]]:
    """
    Minimal JWT-like role parsing.
    Returns (role, subject).
    In production this would verify the Keycloak JWT.
    For now we accept a simple header: 'Bearer ROLE:subject'
    """
    if not authorization:
        return "PUBLIC", None
    try:
        token = authorization.replace("Bearer ", "")
        if ":" in token:
            role, subject = token.split(":", 1)
            return role.upper(), subject
        return "PUBLIC", None
    except Exception:
        return "PUBLIC", None


async def _fire_audit(parcel_id: uuid.UUID, actor_id: str, actor_role: str, purpose: str):
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(
                f"{settings.audit_service_url}/api/v1/audit/events",
                json={
                    "event_type": "PARCEL_VIEWED",
                    "actor_id": actor_id,
                    "actor_role": actor_role,
                    "resource_type": "parcel",
                    "resource_id": str(parcel_id),
                    "parcel_id": str(parcel_id),
                    "purpose": purpose,
                },
            )
    except Exception:
        pass  # fire-and-forget


@router.get("/api/v1/services/parcels/{parcel_id}/profile")
async def parcel_profile(
    parcel_id: uuid.UUID,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    role, subject = _parse_role(authorization)

    # --- Base parcel data ---
    row = await db.execute(
        text(
            """
            SELECT p.id, p.ulpin, p.is_urban,
                   pg.area_sq_m,
                   ST_AsGeoJSON(pg.geometry)::text AS geojson,
                   ror.land_use, ror.data_freshness_status,
                   p.state_code, p.district_code, p.village_code, p.bdpr
            FROM identity.parcels p
            LEFT JOIN geo.parcel_geometries pg ON pg.parcel_id = p.id
            LEFT JOIN revenue.records_of_rights ror ON ror.parcel_id = p.id
            WHERE p.id = :pid AND p.is_active = true
            LIMIT 1
            """
        ),
        {"pid": parcel_id},
    )
    parcel = row.fetchone()
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    pid, ulpin, is_urban, area_sq_m, geojson, land_use, freshness, state_code, district_code, village_code, bdpr = parcel

    geometry = json.loads(geojson) if geojson else None

    # Booleans for public tier
    enc_row = await db.execute(
        text("SELECT EXISTS(SELECT 1 FROM registration.encumbrances WHERE parcel_id=:pid AND is_active=true)"),
        {"pid": parcel_id},
    )
    encumbered = enc_row.scalar() or False

    dispute_row = await db.execute(
        text("SELECT EXISTS(SELECT 1 FROM planning.disputes WHERE parcel_id=:pid AND status='ACTIVE')"),
        {"pid": parcel_id},
    )
    has_dispute = dispute_row.scalar() or False

    # Fire audit (async, non-blocking intent)
    actor = subject or "anonymous"
    import asyncio
    asyncio.create_task(_fire_audit(parcel_id, actor, role, "parcel_profile"))

    # ---- PUBLIC ----
    if role == "PUBLIC":
        return PublicParcelProfile(
            parcel_id=pid, ulpin=ulpin, area_sq_m=area_sq_m,
            land_use=land_use, geometry=geometry,
            is_urban=is_urban, encumbered=encumbered, has_dispute=has_dispute,
        )

    # ---- OFFICER / ADMIN ----
    if role in OFFICER_ROLES or role in ADMIN_ROLES:
        rights_rows = await db.execute(
            text(
                """
                SELECT r.right_type, pa.name_en, r.share
                FROM revenue.rights r
                JOIN revenue.parties pa ON pa.id = r.party_id
                WHERE r.parcel_id = :pid
                """
            ),
            {"pid": parcel_id},
        )
        all_rights = [RightEntry(right_type=r[0], holder_name=r[1] or "Unknown", share=r[2]) for r in rights_rows.fetchall()]

        enc_rows = await db.execute(
            text(
                """
                SELECT encumbrance_type, holder_name, amount, is_active
                FROM registration.encumbrances WHERE parcel_id = :pid
                """
            ),
            {"pid": parcel_id},
        )
        all_enc = [
            EncumbranceEntry(
                encumbrance_type=r[0] or "MORTGAGE",
                holder_name=r[1] or "Financial Institution",
                amount=r[2],
                is_active=r[3],
            )
            for r in enc_rows.fetchall()
        ]

        deed_rows = await db.execute(
            text(
                """
                SELECT deed_type, registration_date::text, consideration_amount
                FROM registration.deeds WHERE parcel_id = :pid ORDER BY registration_date DESC
                """
            ),
            {"pid": parcel_id},
        )
        all_deeds = [DeedEntry(deed_type=r[0], registration_date=r[1], consideration_amount=r[2]) for r in deed_rows.fetchall()]

        dispute_rows = await db.execute(
            text("SELECT case_number, status FROM planning.disputes WHERE parcel_id = :pid"),
            {"pid": parcel_id},
        )
        disputes = [DisputeEntry(case_number=r[0], status=r[1]) for r in dispute_rows.fetchall()]

        cs_rows = await db.execute(
            text(
                """
                SELECT score_type, risk_band, score_value, contributing_factors
                FROM ml.conflict_scores WHERE parcel_id = :pid
                """
            ),
            {"pid": parcel_id},
        )
        conflict_scores = [
            ConflictEntry(score_type=r[0], risk_band=r[1], score_value=r[2], contributing_factors=r[3])
            for r in cs_rows.fetchall()
        ]

        mut_row = await db.execute(
            text(
                """
                SELECT COUNT(*) FROM audit.events
                WHERE parcel_id = :pid AND event_type = 'MUTATION_SUBMITTED'
                  AND payload->>'status' = 'PENDING'
                """
            ),
            {"pid": parcel_id},
        )
        pending_mutations = mut_row.scalar() or 0

        return OfficerParcelProfile(
            parcel_id=pid, ulpin=ulpin, area_sq_m=area_sq_m,
            land_use=land_use, geometry=geometry,
            is_urban=is_urban, encumbered=encumbered, has_dispute=has_dispute,
            state_code=state_code, district_code=district_code,
            village_code=village_code, bdpr=bdpr,
            rights=all_rights, all_rights=all_rights,
            encumbrances=all_enc, all_encumbrances=all_enc,
            disputes=disputes,
            own_deeds=all_deeds, all_deeds=all_deeds,
            conflict_scores=conflict_scores,
            pending_mutation_count=pending_mutations,
            data_freshness_status=freshness,
        )

    # ---- CITIZEN (own parcel or consent-gated) ----
    # Determine ownership
    is_owner = False
    if subject:
        owner_row = await db.execute(
            text(
                """
                SELECT 1 FROM revenue.rights r
                JOIN revenue.parties pa ON pa.id = r.party_id
                WHERE r.parcel_id = :pid
                  AND (pa.aadhaar_hash = :sub OR pa.mobile_hash = :sub OR pa.voter_id_hash = :sub)
                LIMIT 1
                """
            ),
            {"pid": parcel_id, "sub": subject},
        )
        is_owner = owner_row.fetchone() is not None

    if not is_owner and role != "CONSENT_GATED":
        # Authenticated but not owner and no consent → public view
        return PublicParcelProfile(
            parcel_id=pid, ulpin=ulpin, area_sq_m=area_sq_m,
            land_use=land_use, geometry=geometry,
            is_urban=is_urban, encumbered=encumbered, has_dispute=has_dispute,
        )

    # Citizen own / consent-gated
    rights_rows = await db.execute(
        text(
            """
            SELECT r.right_type, pa.name_en, r.share
            FROM revenue.rights r
            JOIN revenue.parties pa ON pa.id = r.party_id
            WHERE r.parcel_id = :pid
            """
        ),
        {"pid": parcel_id},
    )
    rights = [RightEntry(right_type=r[0], holder_name=r[1] or "Unknown", share=r[2]) for r in rights_rows.fetchall()]

    enc_rows = await db.execute(
        text(
            "SELECT encumbrance_type, amount, is_active FROM registration.encumbrances WHERE parcel_id = :pid"
        ),
        {"pid": parcel_id},
    )
    encumbrances = [
        EncumbranceEntry(
            encumbrance_type=r[0] or "MORTGAGE",
            holder_name="Financial Institution",
            amount=r[1],
            is_active=r[2],
        )
        for r in enc_rows.fetchall()
    ]

    dispute_rows = await db.execute(
        text("SELECT case_number, status FROM planning.disputes WHERE parcel_id = :pid"),
        {"pid": parcel_id},
    )
    disputes = [DisputeEntry(case_number=r[0], status=r[1]) for r in dispute_rows.fetchall()]

    deed_rows = await db.execute(
        text(
            """
            SELECT deed_type, registration_date::text, consideration_amount
            FROM registration.deeds WHERE parcel_id = :pid ORDER BY registration_date DESC
            """
        ),
        {"pid": parcel_id},
    )
    own_deeds = [DeedEntry(deed_type=r[0], registration_date=r[1], consideration_amount=r[2]) for r in deed_rows.fetchall()]

    return CitizenOwnParcelProfile(
        parcel_id=pid, ulpin=ulpin, area_sq_m=area_sq_m,
        land_use=land_use, geometry=geometry,
        is_urban=is_urban, encumbered=encumbered, has_dispute=has_dispute,
        rights=rights, encumbrances=encumbrances, disputes=disputes, own_deeds=own_deeds,
    )


@router.get("/api/v1/services/parcels/my")
async def my_parcels(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    _, subject = _parse_role(authorization)
    if not subject:
        raise HTTPException(status_code=401, detail="Authentication required")

    rows = await db.execute(
        text(
            """
            SELECT p.id, p.ulpin, ror.land_use, pg.area_sq_m
            FROM identity.parcels p
            JOIN revenue.rights r ON r.parcel_id = p.id
            JOIN revenue.parties pa ON pa.id = r.party_id
            LEFT JOIN revenue.records_of_rights ror ON ror.parcel_id = p.id
            LEFT JOIN geo.parcel_geometries pg ON pg.parcel_id = p.id
            WHERE (pa.aadhaar_hash = :sub OR pa.mobile_hash = :sub OR pa.voter_id_hash = :sub)
              AND p.is_active = true
            """
        ),
        {"sub": subject},
    )
    parcels = [
        {"parcel_id": str(r[0]), "ulpin": r[1], "land_use": r[2], "area_sq_m": r[3]}
        for r in rows.fetchall()
    ]
    return {"citizen_id": subject, "parcels": parcels}
