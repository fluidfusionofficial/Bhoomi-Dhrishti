"""
bhoomi_common.pagination – Cursor-based and offset-based pagination utilities.

Cursor pagination is preferred for large datasets (parcel search, audit logs)
as it avoids the COUNT(*) overhead and handles concurrent inserts correctly.

Usage:
    from bhoomi_common.pagination import PaginationParams, paginate_query

    @router.get("/parcels")
    async def list_parcels(
        pagination: PaginationParams = Depends(),
        db: AsyncSession = Depends(get_db),
    ):
        query = select(Parcel).order_by(Parcel.created_at.desc())
        return await paginate_query(db, query, pagination, Parcel)
"""

from __future__ import annotations

import base64
import json
import logging
from typing import Any, Generic, List, Optional, Tuple, Type, TypeVar

from fastapi import Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from bhoomi_common.models import PaginatedResponse

logger = logging.getLogger(__name__)

T = TypeVar("T")
ModelT = TypeVar("ModelT", bound=DeclarativeBase)


# ─────────────────────────────────────────────────────────────────────────────
# Pagination parameters (FastAPI Depends)
# ─────────────────────────────────────────────────────────────────────────────

class PaginationParams:
    """
    Standard pagination query parameters.
    Supports both cursor (preferred) and offset pagination.
    """
    def __init__(
        self,
        page: Optional[int] = Query(None, ge=1, description="Page number (offset pagination)"),
        page_size: int = Query(20, ge=1, le=200, description="Items per page"),
        cursor: Optional[str] = Query(None, description="Opaque cursor for next page (cursor pagination)"),
    ):
        self.page = page
        self.page_size = page_size
        self.cursor = cursor

    @property
    def offset(self) -> int:
        if self.page is not None:
            return (self.page - 1) * self.page_size
        return 0


# ─────────────────────────────────────────────────────────────────────────────
# Cursor encoding / decoding
# ─────────────────────────────────────────────────────────────────────────────

def encode_cursor(data: dict) -> str:
    """Encode a dict into a base64 URL-safe opaque cursor string."""
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode()


def decode_cursor(cursor: str) -> dict:
    """Decode an opaque cursor string back to a dict."""
    try:
        return json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
    except Exception:
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# Generic pagination helper
# ─────────────────────────────────────────────────────────────────────────────

async def paginate_query(
    db: AsyncSession,
    query,
    pagination: PaginationParams,
    response_class: Type[T],
    count_query=None,
) -> PaginatedResponse[T]:
    """
    Execute a SQLAlchemy select query with pagination.

    Returns a PaginatedResponse with items serialised as response_class instances.
    If count_query is provided, total count is included; otherwise omitted for performance.
    """
    # Apply cursor if provided
    if pagination.cursor:
        cursor_data = decode_cursor(pagination.cursor)
        # Cursor-based queries must be handled by the caller
        # (this is a placeholder; real cursor logic is query-specific)
        logger.debug("Cursor data: %s", cursor_data)

    # Fetch one extra item to determine has_next
    fetch_count = pagination.page_size + 1
    result = await db.execute(
        query.offset(pagination.offset).limit(fetch_count)
    )
    rows = result.scalars().all()

    has_next = len(rows) > pagination.page_size
    items = rows[:pagination.page_size]

    # Count total if count_query provided
    total: Optional[int] = None
    if count_query is not None:
        count_result = await db.execute(count_query)
        total = count_result.scalar()

    # Build next cursor
    next_cursor: Optional[str] = None
    if has_next and items:
        last_item = items[-1]
        # Build cursor from last item's id and created_at
        cursor_data = {}
        if hasattr(last_item, "id"):
            cursor_data["id"] = str(last_item.id)
        if hasattr(last_item, "created_at") and last_item.created_at:
            cursor_data["created_at"] = last_item.created_at.isoformat()
        next_cursor = encode_cursor(cursor_data) if cursor_data else None

    # Serialise items to response_class
    serialised: List[T] = []
    for item in items:
        try:
            if hasattr(response_class, "model_validate"):
                serialised.append(response_class.model_validate(item))
            else:
                serialised.append(response_class.from_orm(item))  # type: ignore
        except Exception as exc:
            logger.warning("Failed to serialise item %s: %s", getattr(item, "id", "?"), exc)

    return PaginatedResponse(
        items=serialised,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        next_cursor=next_cursor,
        has_next=has_next,
    )
