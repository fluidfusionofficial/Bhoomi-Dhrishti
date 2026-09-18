import asyncio
import httpx
from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.db import get_db
from app.models.revenue import Mutation, RecordOfRights, Right
from app.schemas.revenue import (
    MutationResponse,
    ProvenanceInfo,
    RecordOfRightsResponse,
    RightDetail,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Audit helper
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
# Helpers
# ---------------------------------------------------------------------------

def _build_right_detail(right: Right) -> RightDetail:
    share_display: str | None = None
    if right.share_numerator is not None and right.share_denominator is not None:
        share_display = f"{right.share_numerator}/{right.share_denominator}"
    return RightDetail(
        id=right.id,
        right_type=right.right_type,
        party_id=right.party_id,
        party=right.party,  # selectin-loaded
        share_numerator=right.share_numerator,
        share_denominator=right.share_denominator,
        share_display=share_display,
        valid_from=right.valid_from,
        valid_to=right.valid_to,
    )


def _build_provenance(ror: RecordOfRights) -> ProvenanceInfo:
    dept = ror.source_department or "Unknown Department"
    as_of = ror.source_as_of_date or date.today()
    freshness = ror.data_freshness_status or "DEMO"
    return ProvenanceInfo(
        source_department=dept,
        source_system="State Revenue Portal",
        state_code="IN",
        as_of_date=as_of,
        data_freshness_status=freshness,  # type: ignore[arg-type]
        last_synced_at=None,
        source_url=None,
    )


def _build_coverage_note(ror: RecordOfRights) -> str:
    dept = ror.source_department or "Unknown Department"
    synced = ror.source_as_of_date or date.today()
    return f"Record from {dept}, last synced {synced}"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/parcels/{parcel_id}/ror", response_model=RecordOfRightsResponse)
async def get_record_of_rights(
    parcel_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Return the Record of Rights (RoR) for a parcel, with rights and party details."""
    stmt = (
        select(RecordOfRights)
        .where(RecordOfRights.parcel_id == parcel_id)
        .options(
            selectinload(RecordOfRights.rights).selectinload(Right.party)
        )
        .order_by(RecordOfRights.record_date.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    ror = result.scalar_one_or_none()

    if ror is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"No Record of Rights found for parcel {parcel_id}",
                    "detail": {"parcel_id": str(parcel_id)},
                }
            },
        )

    emit_audit(request, "READ_ROR", "records_of_rights", ror.id)

    rights_detail = [_build_right_detail(r) for r in ror.rights]
    provenance = _build_provenance(ror)
    coverage_note = _build_coverage_note(ror)

    return RecordOfRightsResponse(
        id=ror.id,
        parcel_id=ror.parcel_id,
        ror_id=ror.ror_id,
        record_date=ror.record_date,
        survey_number=ror.survey_number,
        land_classification=ror.land_classification,
        land_use=ror.land_use,
        area_sq_m=ror.area_sq_m,
        area_native=ror.area_native,
        area_unit_native=ror.area_unit_native,
        rights=rights_detail,
        provenance=provenance,
        coverage_note=coverage_note,
    )


@router.get("/parcels/{parcel_id}/rights")
async def get_rights_for_parcel(
    parcel_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Return all rights entries for a parcel with party details."""
    stmt = (
        select(Right)
        .where(Right.parcel_id == parcel_id)
        .options(selectinload(Right.party))
        .order_by(Right.valid_from.desc())
    )
    result = await db.execute(stmt)
    rights = result.scalars().all()

    emit_audit(request, "READ_RIGHTS", "rights", parcel_id)

    return {"parcel_id": str(parcel_id), "rights": [_build_right_detail(r).model_dump() for r in rights]}


@router.get("/parcels/{parcel_id}/mutations", response_model=list[MutationResponse])
async def get_mutations_for_parcel(
    parcel_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Return all mutations for a parcel ordered by submitted_at DESC."""
    stmt = (
        select(Mutation)
        .where(Mutation.parcel_id == parcel_id)
        .order_by(Mutation.submitted_at.desc())
    )
    result = await db.execute(stmt)
    mutations = result.scalars().all()

    emit_audit(request, "READ_MUTATIONS", "mutations", parcel_id)

    return mutations


@router.get("/ror/{parcel_id}/history")
async def get_ror_history(
    parcel_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Return temporal ownership history for a parcel.

    Shows all historical rights and ownership changes over time,
    ordered by valid_from date descending (most recent first).

    Each entry includes:
    - Right type (OWNER, LESSEE, MORTGAGEE, etc.)
    - Party details with share
    - Validity period (valid_from to valid_to)
    - Source attribution with as-of date
    """
    stmt = (
        select(Right)
        .where(Right.parcel_id == parcel_id)
        .options(selectinload(Right.party))
        .order_by(Right.valid_from.desc().nulls_last(), Right.created_at.desc())
    )
    result = await db.execute(stmt)
    rights = result.scalars().all()

    emit_audit(request, "READ_ROR_HISTORY", "rights", parcel_id)

    # Build temporal history
    history = []
    for right in rights:
        share_display = None
        if right.share_numerator is not None and right.share_denominator is not None:
            share_display = f"{right.share_numerator}/{right.share_denominator}"

        entry = {
            "id": str(right.id),
            "right_type": right.right_type,
            "party": {
                "id": str(right.party.id) if right.party else None,
                "name_en": right.party.name_en if right.party else None,
                "name_local": right.party.name_local if right.party else None,
                "party_type": right.party.party_type if right.party else None,
            } if right.party else None,
            "share_numerator": right.share_numerator,
            "share_denominator": right.share_denominator,
            "share_display": share_display,
            "valid_from": right.valid_from.isoformat() if right.valid_from else None,
            "valid_to": right.valid_to.isoformat() if right.valid_to else None,
            "created_at": right.created_at.isoformat() if right.created_at else None,
        }
        history.append(entry)

    return {
        "parcel_id": str(parcel_id),
        "total_entries": len(history),
        "history": history,
        "source_attribution": {
            "source_department": "Revenue Department",
            "source_system": "State Revenue Portal",
            "as_of_date": date.today().isoformat(),
            "data_freshness_status": "CACHED",
            "completeness_note": "Historical records may be incomplete for parcels created before digital record-keeping. Earliest digital record dates vary by state.",
        },
    }
