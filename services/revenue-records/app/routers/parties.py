import asyncio
import uuid
from typing import List

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.models.revenue import Party
from app.schemas.revenue import PartyResponse

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
# Routes — IMPORTANT: /search must be declared BEFORE /{party_id}
# ---------------------------------------------------------------------------

@router.get("/parties/search", response_model=List[PartyResponse])
async def search_parties(
    q: str = Query(..., min_length=1, description="Search string for name_en, name_local or name_phonetic_key"),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Search parties by name (ILIKE on name_en / name_local) and by phonetic key.
    Results from both strategies are deduplicated by id.
    """
    pattern = f"%{q}%"

    # Strategy 1: ILIKE on human-readable name columns
    ilike_stmt = text(
        """
        SELECT id, party_type, name_en, name_local, name_phonetic_key
        FROM revenue.parties
        WHERE name_en ILIKE :pattern
           OR name_local ILIKE :pattern
        LIMIT 50
        """
    )

    # Strategy 2: ILIKE on phonetic key
    phonetic_stmt = text(
        """
        SELECT id, party_type, name_en, name_local, name_phonetic_key
        FROM revenue.parties
        WHERE name_phonetic_key ILIKE :pattern
        LIMIT 50
        """
    )

    ilike_result = await db.execute(ilike_stmt, {"pattern": pattern})
    phonetic_result = await db.execute(phonetic_stmt, {"pattern": pattern})

    seen: dict[uuid.UUID, dict] = {}

    for row in ilike_result.mappings():
        rid = row["id"]
        if rid not in seen:
            seen[rid] = dict(row)

    for row in phonetic_result.mappings():
        rid = row["id"]
        if rid not in seen:
            seen[rid] = dict(row)

    if request is not None:
        emit_audit(request, "SEARCH_PARTIES", "parties", q)

    return [PartyResponse(**record) for record in seen.values()]


@router.get("/parties/{party_id}", response_model=PartyResponse)
async def get_party(
    party_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single party by UUID."""
    stmt = select(Party).where(Party.id == party_id)
    result = await db.execute(stmt)
    party = result.scalar_one_or_none()

    if party is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Party {party_id} not found",
                    "detail": {"party_id": str(party_id)},
                }
            },
        )

    emit_audit(request, "READ_PARTY", "parties", party_id)

    return party
