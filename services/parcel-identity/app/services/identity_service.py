"""
identity_service – Business logic for parcel identity resolution and management.

All database writes set updated_at via server-side `NOW()` so timestamps are
always in sync with the PostgreSQL clock, never the application server clock.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import Parcel, ParcelAlias, ParcelLineage
from app.schemas.identity import (
    CreateParcelRequest,
    ParcelIdentityResponse,
    ProvenanceInfo,
    PromoteUlpinRequest,
)
from bhoomi_common.errors import BhoomiNotFound, BhoomiConflict

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# BDPR generation
# ---------------------------------------------------------------------------

async def generate_bdpr(state_code: str, db: AsyncSession) -> str:
    """
    Generate a unique Bhoomi Dhrishti Parcel Reference.

    Format: BD-{STATE_CODE_UPPER}-{8_HEX_UPPER}
    Example: BD-TN-A3F12B9C

    Retries until a non-colliding value is produced (collision probability
    is ~1 in 4 billion, so the loop almost never iterates more than once).
    """
    for _ in range(10):  # safety bound against pathological collision runs
        candidate = f"BD-{state_code.upper()}-{secrets.token_hex(4).upper()}"
        result = await db.execute(
            select(Parcel.id).where(Parcel.bdpr == candidate)
        )
        if result.scalar_one_or_none() is None:
            return candidate
    raise RuntimeError(
        f"Could not generate unique BDPR for state_code={state_code} after 10 attempts"
    )


# ---------------------------------------------------------------------------
# Provenance builder
# ---------------------------------------------------------------------------

def _build_provenance(parcel: Parcel) -> ProvenanceInfo:
    """
    Synthesise a ProvenanceInfo from the available identity record fields.

    Since identity.parcels does not store a full provenance block, we
    derive one: data retrieved directly from the DB is LIVE; the source
    system is the ULPIN assigner when known, otherwise the platform itself.
    """
    source_system = parcel.ulpin_source or "BHOOMI_DHRISHTI"
    return ProvenanceInfo(
        source_department="Revenue Department",
        source_system=source_system,
        state_code=parcel.state_code,
        as_of_date=parcel.updated_at.date() if parcel.updated_at else datetime.now(timezone.utc).date(),
        data_freshness_status="LIVE",
        last_synced_at=parcel.updated_at,
    )


# ---------------------------------------------------------------------------
# ORM → schema conversion
# ---------------------------------------------------------------------------

def _to_response(parcel: Parcel) -> ParcelIdentityResponse:
    return ParcelIdentityResponse(
        id=parcel.id,
        bdpr=parcel.bdpr,
        ulpin=parcel.ulpin,
        ulpin_is_authoritative=parcel.ulpin is not None,
        state_code=parcel.state_code,
        district_code=parcel.district_code,
        subdistrict_code=parcel.subdistrict_code,
        village_code=parcel.village_code,
        urban_ward_code=parcel.urban_ward_code,
        is_urban=parcel.is_urban,
        is_active=parcel.is_active,
        created_at=parcel.created_at,
        updated_at=parcel.updated_at,
        system_of_record_flag=parcel.system_of_record_flag,
        provenance=_build_provenance(parcel),
    )


# ---------------------------------------------------------------------------
# Resolve identifier (BDPR, ULPIN, or alias)
# ---------------------------------------------------------------------------

async def resolve_parcel(identifier: str, db: AsyncSession) -> ParcelIdentityResponse:
    """
    Resolve a parcel by BDPR (exact), ULPIN (exact), or alias value lookup.
    Returns a full ParcelIdentityResponse or raises BhoomiNotFound.
    """
    # 1. Try BDPR exact match (most common path)
    result = await db.execute(
        select(Parcel).where(Parcel.bdpr == identifier, Parcel.is_active == True)
    )
    parcel = result.scalar_one_or_none()
    if parcel:
        logger.debug("parcel.resolved", via="bdpr", identifier=identifier)
        return _to_response(parcel)

    # 2. Try ULPIN exact match
    result = await db.execute(
        select(Parcel).where(Parcel.ulpin == identifier, Parcel.is_active == True)
    )
    parcel = result.scalar_one_or_none()
    if parcel:
        logger.debug("parcel.resolved", via="ulpin", identifier=identifier)
        return _to_response(parcel)

    # 3. Try alias table (survey number, khasra, etc.)
    alias_result = await db.execute(
        select(ParcelAlias).where(ParcelAlias.alias_value == identifier)
    )
    alias = alias_result.scalar_one_or_none()
    if alias:
        parcel_result = await db.execute(
            select(Parcel).where(Parcel.id == alias.parcel_id, Parcel.is_active == True)
        )
        parcel = parcel_result.scalar_one_or_none()
        if parcel:
            logger.debug("parcel.resolved", via="alias", identifier=identifier)
            return _to_response(parcel)

    raise BhoomiNotFound(resource="Parcel", id=identifier)


# ---------------------------------------------------------------------------
# Create parcel
# ---------------------------------------------------------------------------

async def create_parcel(
    req: CreateParcelRequest, db: AsyncSession
) -> ParcelIdentityResponse:
    bdpr = await generate_bdpr(req.state_code, db)

    parcel = Parcel(
        id=uuid.uuid4(),
        bdpr=bdpr,
        state_code=req.state_code.upper(),
        district_code=req.district_code.upper(),
        subdistrict_code=req.subdistrict_code,
        village_code=req.village_code,
        urban_ward_code=req.urban_ward_code,
        is_urban=req.is_urban,
        is_active=True,
        system_of_record_flag="DERIVED",
    )
    db.add(parcel)

    # Register initial survey number as an alias if provided
    if req.initial_survey_number:
        alias = ParcelAlias(
            id=uuid.uuid4(),
            parcel_id=parcel.id,
            alias_type="SURVEY_NUMBER",
            alias_value=req.initial_survey_number,
            source_system="BHOOMI_DHRISHTI",
        )
        db.add(alias)

    await db.flush()  # populate server defaults (created_at etc.) without committing
    await db.refresh(parcel)

    logger.info("parcel.created", bdpr=parcel.bdpr, state=parcel.state_code)
    return _to_response(parcel)


# ---------------------------------------------------------------------------
# Promote ULPIN
# ---------------------------------------------------------------------------

async def promote_ulpin(
    parcel_id: uuid.UUID, req: PromoteUlpinRequest, db: AsyncSession
) -> ParcelIdentityResponse:
    result = await db.execute(
        select(Parcel).where(Parcel.id == parcel_id)
    )
    parcel = result.scalar_one_or_none()
    if parcel is None:
        raise BhoomiNotFound(resource="Parcel", id=str(parcel_id))

    if parcel.ulpin is not None:
        raise BhoomiConflict(
            f"ULPIN_ALREADY_SET: parcel {parcel_id} already has ULPIN {parcel.ulpin!r}"
        )

    parcel.ulpin = req.ulpin
    parcel.ulpin_source = req.ulpin_source
    parcel.ulpin_assigned_at = req.ulpin_assigned_at or datetime.now(timezone.utc)
    parcel.system_of_record_flag = "AUTHORITATIVE"

    await db.flush()
    await db.refresh(parcel)

    logger.info(
        "parcel.ulpin_promoted",
        parcel_id=str(parcel_id),
        ulpin=req.ulpin,
        source=req.ulpin_source,
    )
    return _to_response(parcel)


# ---------------------------------------------------------------------------
# Lineage
# ---------------------------------------------------------------------------

async def get_lineage(parcel_id: uuid.UUID, db: AsyncSession) -> dict:
    """Return the lineage tree for a parcel: {parcel, parents, children}."""
    # Verify parcel exists
    parcel_result = await db.execute(
        select(Parcel).where(Parcel.id == parcel_id)
    )
    parcel = parcel_result.scalar_one_or_none()
    if parcel is None:
        raise BhoomiNotFound(resource="Parcel", id=str(parcel_id))

    # Events where this parcel is the child (i.e. events that created it)
    parents_result = await db.execute(
        select(ParcelLineage).where(ParcelLineage.child_parcel_id == parcel_id)
    )
    parents = parents_result.scalars().all()

    # Events where this parcel is the parent (i.e. events that split it)
    children_result = await db.execute(
        select(ParcelLineage).where(ParcelLineage.parent_parcel_id == parcel_id)
    )
    children = children_result.scalars().all()

    return {
        "parcel": _to_response(parcel),
        "parents": parents,
        "children": children,
    }


# ---------------------------------------------------------------------------
# Aliases
# ---------------------------------------------------------------------------

async def get_aliases(parcel_id: uuid.UUID, db: AsyncSession) -> dict:
    parcel_result = await db.execute(
        select(Parcel.id).where(Parcel.id == parcel_id)
    )
    if parcel_result.scalar_one_or_none() is None:
        raise BhoomiNotFound(resource="Parcel", id=str(parcel_id))

    aliases_result = await db.execute(
        select(ParcelAlias).where(ParcelAlias.parcel_id == parcel_id)
    )
    return {
        "parcel_id": parcel_id,
        "aliases": aliases_result.scalars().all(),
    }


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

async def search_parcels(
    db: AsyncSession,
    state_code: str | None,
    district_code: str | None,
    village_code: str | None,
    survey_number: str | None,
    page: int,
    page_size: int,
) -> dict:
    """
    Multi-field parcel search.

    When survey_number is provided, we first find matching parcel IDs via
    the aliases table, then filter the parcels table accordingly.
    """
    from sqlalchemy import func as sqlfunc

    stmt = select(Parcel).where(Parcel.is_active == True)

    if state_code:
        stmt = stmt.where(Parcel.state_code == state_code.upper())
    if district_code:
        stmt = stmt.where(Parcel.district_code == district_code.upper())
    if village_code:
        stmt = stmt.where(Parcel.village_code == village_code)
    if survey_number:
        # Join through aliases
        alias_sub = (
            select(ParcelAlias.parcel_id)
            .where(
                ParcelAlias.alias_type == "SURVEY_NUMBER",
                ParcelAlias.alias_value == survey_number,
            )
            .scalar_subquery()
        )
        stmt = stmt.where(Parcel.id.in_(alias_sub))

    # Count total
    count_stmt = select(sqlfunc.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # Paginate
    offset = (page - 1) * page_size
    stmt = stmt.order_by(Parcel.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    parcels = result.scalars().all()

    return {
        "items": parcels,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
