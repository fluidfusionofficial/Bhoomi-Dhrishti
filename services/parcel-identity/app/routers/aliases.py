"""Parcel alias lookup and management endpoints."""

from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from bhoomi_common.auth import Actor, get_current_actor
from bhoomi_common.db import get_db

router = APIRouter()


@router.get("/{alias_type}/{alias_value}", summary="Resolve alias to BDPR")
async def resolve_alias(
    alias_type: str,
    alias_value: str,
    source_system: str = None,
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    """
    Resolve a state-specific parcel identifier (survey number, PID, khasra, etc.)
    to its canonical Bhoomi Dhrishti Parcel Reference (BDPR).
    """
    from bhoomi_common.errors import BhoomiNotFound
    raise BhoomiNotFound("Alias", f"{alias_type}/{alias_value}")


@router.get("/parcel/{parcel_id}", summary="List all aliases for a parcel")
async def list_aliases(
    parcel_id: UUID,
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    """List all known aliases (survey numbers, PIDs, khasra, etc.) for a parcel."""
    return {"parcel_id": str(parcel_id), "aliases": []}
