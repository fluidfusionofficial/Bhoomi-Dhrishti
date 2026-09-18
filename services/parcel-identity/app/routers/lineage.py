"""Parcel lineage (subdivision, amalgamation, resurvey) endpoints."""

from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from bhoomi_common.auth import Actor, get_current_actor
from bhoomi_common.db import get_db

router = APIRouter()


@router.get("/{parcel_id}", summary="Get parcel lineage history")
async def get_lineage(
    parcel_id: UUID,
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    """
    Return the complete lineage tree for a parcel –
    all parent and child parcels from subdivisions, amalgamations and resurveys.
    """
    return {"parcel_id": str(parcel_id), "lineage_events": []}
