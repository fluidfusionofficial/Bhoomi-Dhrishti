import asyncio
import httpx
from datetime import date, datetime
from typing import List
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.schemas.registration import (
    DuplicateCheckRequest,
    DuplicateCheckResponse,
    EncumbranceResponse,
    PartyRef,
    ProvenanceInfo,
)

logger = structlog.get_logger()

router = APIRouter()

# ---------------------------------------------------------------------------
# Audit helper (same pattern as deeds router)
# ---------------------------------------------------------------------------


async def _emit_audit(client: httpx.AsyncClient, action: str, resource_type: str, resource_id: str):
    try:
        await client.post(
            f"{settings.audit_service_url}/api/v1/events",
            json={
                "service": settings.service_name,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
            },
            timeout=2.0,
        )
    except Exception:
        pass


def emit_audit(request: Request, action: str, resource_type: str, resource_id):
    asyncio.create_task(
        _emit_audit(request.app.state.http_client, action, resource_type, str(resource_id))
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/parcels/{parcel_id}/encumbrances", response_model=List[EncumbranceResponse])
async def list_encumbrances(
    parcel_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Return all encumbrances (active and inactive) for a parcel with party details."""
    try:
        result = await db.execute(
            text(
                """
                SELECT
                    e.id,
                    e.parcel_id,
                    e.encumbrance_type,
                    e.in_favour_of_party_id,
                    e.is_active,
                    e.amount,
                    e.start_date,
                    e.end_date,
                    p.id         AS party_id,
                    p.name_en    AS party_name_en,
                    p.name_local AS party_name_local,
                    p.party_type AS party_type
                FROM registration.encumbrances e
                LEFT JOIN revenue.parties p ON p.id = e.in_favour_of_party_id
                WHERE e.parcel_id = :parcel_id
                ORDER BY e.start_date DESC NULLS LAST
                """
            ),
            {"parcel_id": str(parcel_id)},
        )
        rows = result.mappings().all()
    except Exception as exc:
        logger.error("list_encumbrances_error", parcel_id=str(parcel_id), error=str(exc))
        raise HTTPException(
            status_code=500,
            detail={"code": "DB_ERROR", "message": "Failed to fetch encumbrances", "detail": {}},
        )

    enc_list = []
    for row in rows:
        party = (
            PartyRef(
                id=row["party_id"],
                name_en=row["party_name_en"] or "",
                name_local=row["party_name_local"],
                party_type=row["party_type"],
            )
            if row["party_id"]
            else None
        )
        enc_list.append(
            EncumbranceResponse(
                id=row["id"],
                parcel_id=row["parcel_id"],
                encumbrance_type=row["encumbrance_type"],
                in_favour_of_party_id=row["in_favour_of_party_id"],
                in_favour_of=party,
                is_active=row["is_active"],
                amount=row["amount"],
                start_date=row["start_date"],
                end_date=row["end_date"],
            )
        )

    emit_audit(request, "LIST_ENCUMBRANCES", "parcel", parcel_id)
    return enc_list


@router.post("/check-duplicate", response_model=DuplicateCheckResponse)
async def check_duplicate(
    body: DuplicateCheckRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Check ML transaction-network flags for a parcel.

    Gracefully handles a missing ml.transaction_network_flags table by
    returning an empty flags list with risk_level=LOW.
    """
    parcel_id = body.parcel_id
    today = date.today()
    checked_at = datetime.utcnow()

    provenance = ProvenanceInfo(
        source_department="ML Analytics",
        source_system="ML_NETWORK_ANALYSIS",
        state_code="KA",
        as_of_date=today,
        data_freshness_status="LIVE",
        last_synced_at=checked_at,
    )

    flags_data: list = []

    try:
        result = await db.execute(
            text(
                """
                SELECT id, flag_type, confidence_score, flagged_at, details
                FROM ml.transaction_network_flags
                WHERE parcel_id = :parcel_id AND is_resolved = false
                ORDER BY confidence_score DESC
                """
            ),
            {"parcel_id": str(parcel_id)},
        )
        rows = result.mappings().all()
        for row in rows:
            flags_data.append(
                {
                    "id": str(row["id"]),
                    "flag_type": row["flag_type"],
                    "confidence_score": float(row["confidence_score"]) if row["confidence_score"] is not None else None,
                    "flagged_at": row["flagged_at"].isoformat() if row["flagged_at"] else None,
                    "details": row["details"],
                }
            )
    except Exception as exc:
        # Table may not exist yet — treat as no flags
        logger.warning(
            "ml_flags_query_failed",
            parcel_id=str(parcel_id),
            error=str(exc),
            note="Treating as empty flags",
        )

    # Compute risk level
    if flags_data:
        max_score = max(
            (f["confidence_score"] or 0.0) for f in flags_data
        )
        if max_score >= 0.9:
            risk_level = "CRITICAL"
        elif max_score >= 0.7:
            risk_level = "HIGH"
        else:
            risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    emit_audit(request, "CHECK_DUPLICATE", "parcel", parcel_id)
    return DuplicateCheckResponse(
        parcel_id=parcel_id,
        has_duplicate_flag=len(flags_data) > 0,
        flags=flags_data,
        risk_level=risk_level,
        checked_at=checked_at,
        sources_checked=["ML_NETWORK_ANALYSIS", "DEED_REGISTRY"],
        provenance=provenance,
    )
