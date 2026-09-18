"""
Review queue endpoints for human verification of entity resolution matches.

Officers can approve or reject candidate linkages that were flagged by the
probabilistic/phonetic resolvers with confidence scores between thresholds.
"""

from __future__ import annotations

import uuid
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from bhoomi_common.auth import Actor, get_current_actor, require_roles
from bhoomi_common.audit import AuditEventType, emit_audit_event
from bhoomi_common.pagination import PaginatedResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/reviews", tags=["Review Queue"])


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────

class ReviewQueueItem(BaseModel):
    """A pending review item."""
    id: uuid.UUID
    source_type: str
    source_record_id: str
    target_parcel_id: uuid.UUID
    confidence_score: float
    match_method: str
    evidence: dict
    source_record_preview: Optional[dict] = None
    target_parcel_bdpr: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}


class ReviewDecisionRequest(BaseModel):
    """Request to approve or reject a review item."""
    reviewer_notes: Optional[str] = Field(None, max_length=500)


class ReviewDecisionResponse(BaseModel):
    """Response after review decision."""
    link_id: uuid.UUID
    decision: str  # APPROVED | REJECTED
    updated_at: str


# ─────────────────────────────────────────────────────────────────────────────
# GET /reviews/queue - Pending reviews
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/queue",
    response_model=PaginatedResponse[ReviewQueueItem],
    summary="Get pending review queue",
    dependencies=[Depends(require_roles(["revenue_officer", "district_collector"]))],
)
async def get_review_queue(
    source_type: Optional[str] = Query(None, description="Filter by source type"),
    state_code: Optional[str] = Query(None, description="Filter by state"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ReviewQueueItem]:
    """
    Retrieve pending review queue items.

    Only revenue officers and district collectors can access the review queue.
    Items are ordered by confidence score descending (highest confidence first).
    """

    # Build query
    where_clauses = ["rq.status = 'PENDING'"]
    params = {"offset": (page - 1) * page_size, "limit": page_size}

    if source_type:
        where_clauses.append("rq.source_type = :source_type")
        params["source_type"] = source_type

    if state_code or actor.state_code:
        # Officers can only see reviews for their state
        effective_state = state_code or actor.state_code
        where_clauses.append("p.state_code = :state_code")
        params["state_code"] = effective_state

    where_sql = " AND ".join(where_clauses)

    # Get total count
    count_query = text(f"""
        SELECT COUNT(*)
        FROM identity.review_queue rq
        JOIN identity.parcels p ON p.id = rq.target_parcel_id
        WHERE {where_sql}
    """)

    count_result = await db.execute(count_query, params)
    total = count_result.scalar_one()

    # Get paginated results
    query = text(f"""
        SELECT
            rq.id,
            rq.source_type,
            rq.source_record_id,
            rq.target_parcel_id,
            rq.confidence_score,
            rq.match_method,
            rq.evidence_json as evidence,
            rq.source_record_json as source_record_preview,
            p.bdpr as target_parcel_bdpr,
            rq.created_at
        FROM identity.review_queue rq
        JOIN identity.parcels p ON p.id = rq.target_parcel_id
        WHERE {where_sql}
        ORDER BY rq.confidence_score DESC, rq.created_at ASC
        OFFSET :offset LIMIT :limit
    """)

    result = await db.execute(query, params)
    rows = result.mappings().all()

    items = [ReviewQueueItem(**dict(row)) for row in rows]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /reviews/{link_id}/approve - Approve match
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/{link_id}/approve",
    response_model=ReviewDecisionResponse,
    summary="Approve a candidate match",
    dependencies=[Depends(require_roles(["revenue_officer", "district_collector"]))],
)
async def approve_review(
    link_id: uuid.UUID,
    req: ReviewDecisionRequest,
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
) -> ReviewDecisionResponse:
    """
    Approve a candidate linkage, promoting it to CONFIRMED status.

    This creates a confirmed link in identity.parcel_links and removes
    the item from the review queue.
    """

    # Fetch the review item
    fetch_query = text("""
        SELECT
            rq.source_type, rq.source_record_id, rq.target_parcel_id,
            rq.confidence_score, rq.match_method, rq.evidence_json,
            p.state_code
        FROM identity.review_queue rq
        JOIN identity.parcels p ON p.id = rq.target_parcel_id
        WHERE rq.id = :link_id AND rq.status = 'PENDING'
    """)

    result = await db.execute(fetch_query, {"link_id": link_id})
    row = result.mappings().one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review item {link_id} not found or already processed",
        )

    # Check officer has access to this state
    if actor.state_code and actor.state_code != row["state_code"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to review items for this state",
        )

    # Create confirmed link
    insert_link = text("""
        INSERT INTO identity.parcel_links
            (source_type, source_id, target_parcel_id, confidence_score,
             match_method, evidence_json, status, reviewed_by, reviewed_at)
        VALUES
            (:source_type, :source_id, :target_parcel_id, :confidence_score,
             :match_method, :evidence_json::jsonb, 'CONFIRMED', :reviewed_by, NOW())
        ON CONFLICT (source_id, source_type)
        DO UPDATE SET
            target_parcel_id = EXCLUDED.target_parcel_id,
            confidence_score = EXCLUDED.confidence_score,
            status = 'CONFIRMED',
            reviewed_by = EXCLUDED.reviewed_by,
            reviewed_at = NOW()
    """)

    await db.execute(insert_link, {
        "source_type": row["source_type"],
        "source_id": row["source_record_id"],
        "target_parcel_id": row["target_parcel_id"],
        "confidence_score": row["confidence_score"],
        "match_method": row["match_method"],
        "evidence_json": row["evidence_json"],
        "reviewed_by": actor.subject,
    })

    # Mark review item as approved
    update_query = text("""
        UPDATE identity.review_queue
        SET status = 'APPROVED',
            reviewed_by = :reviewed_by,
            reviewed_at = NOW(),
            reviewer_notes = :notes
        WHERE id = :link_id
        RETURNING updated_at
    """)

    update_result = await db.execute(update_query, {
        "link_id": link_id,
        "reviewed_by": actor.subject,
        "notes": req.reviewer_notes,
    })
    updated_row = update_result.mappings().one()

    await db.commit()

    # Emit audit event
    await emit_audit_event(
        event_type="REVIEW_APPROVED",
        actor=actor,
        resource_type="REVIEW_QUEUE_ITEM",
        resource_id=link_id,
        parcel_id=row["target_parcel_id"],
        payload={
            "source_type": row["source_type"],
            "source_record_id": row["source_record_id"],
            "match_method": row["match_method"],
        },
    )

    logger.info(
        "review_approved",
        link_id=str(link_id),
        parcel_id=str(row["target_parcel_id"]),
        reviewer=actor.subject,
    )

    return ReviewDecisionResponse(
        link_id=link_id,
        decision="APPROVED",
        updated_at=str(updated_row["updated_at"]),
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /reviews/{link_id}/reject - Reject match
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/{link_id}/reject",
    response_model=ReviewDecisionResponse,
    summary="Reject a candidate match",
    dependencies=[Depends(require_roles(["revenue_officer", "district_collector"]))],
)
async def reject_review(
    link_id: uuid.UUID,
    req: ReviewDecisionRequest,
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
) -> ReviewDecisionResponse:
    """
    Reject a candidate linkage, marking it as a false match.

    This removes the item from the review queue and optionally records
    the rejection reason for future model training.
    """

    # Fetch the review item
    fetch_query = text("""
        SELECT rq.target_parcel_id, p.state_code
        FROM identity.review_queue rq
        JOIN identity.parcels p ON p.id = rq.target_parcel_id
        WHERE rq.id = :link_id AND rq.status = 'PENDING'
    """)

    result = await db.execute(fetch_query, {"link_id": link_id})
    row = result.mappings().one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review item {link_id} not found or already processed",
        )

    # Check officer has access to this state
    if actor.state_code and actor.state_code != row["state_code"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to review items for this state",
        )

    # Mark review item as rejected
    update_query = text("""
        UPDATE identity.review_queue
        SET status = 'REJECTED',
            reviewed_by = :reviewed_by,
            reviewed_at = NOW(),
            reviewer_notes = :notes
        WHERE id = :link_id
        RETURNING updated_at
    """)

    update_result = await db.execute(update_query, {
        "link_id": link_id,
        "reviewed_by": actor.subject,
        "notes": req.reviewer_notes,
    })
    updated_row = update_result.mappings().one()

    await db.commit()

    # Emit audit event
    await emit_audit_event(
        event_type="REVIEW_REJECTED",
        actor=actor,
        resource_type="REVIEW_QUEUE_ITEM",
        resource_id=link_id,
        parcel_id=row["target_parcel_id"],
        payload={"rejection_reason": req.reviewer_notes},
    )

    logger.info(
        "review_rejected",
        link_id=str(link_id),
        reviewer=actor.subject,
        reason=req.reviewer_notes,
    )

    return ReviewDecisionResponse(
        link_id=link_id,
        decision="REJECTED",
        updated_at=str(updated_row["updated_at"]),
    )
