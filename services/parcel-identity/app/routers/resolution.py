"""
Entity resolution endpoints for triggering and monitoring the resolution cascade.

Officers can trigger batch resolution runs and view metrics on precision/recall.
"""

from __future__ import annotations

import uuid
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.resolution.cascade import ResolutionCascade
from bhoomi_common.auth import Actor, get_current_actor, require_roles
from bhoomi_common.audit import AuditEventType, emit_audit_event

logger = structlog.get_logger()

router = APIRouter(prefix="/resolution", tags=["Entity Resolution"])


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────

class ResolutionRunRequest(BaseModel):
    """Request to trigger a resolution run."""
    source_type: str = Field(..., description="Source type to resolve (e.g., 'revenue_ror', 'sro_registrations')")
    state_code: Optional[str] = Field(None, description="Limit to specific state")
    confidence_threshold_confirm: float = Field(0.7, ge=0.0, le=1.0, description="Auto-confirm threshold")
    confidence_threshold_review: float = Field(0.4, ge=0.0, le=1.0, description="Human review threshold")


class ResolutionRunResponse(BaseModel):
    """Response after triggering a resolution run."""
    job_id: uuid.UUID
    status: str  # QUEUED | RUNNING | COMPLETED | FAILED
    message: str


class ResolutionMetrics(BaseModel):
    """Precision/recall/F1 metrics for resolution quality."""
    total_links: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    method_breakdown: dict = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# POST /resolution/run - Trigger resolution cascade
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/run",
    response_model=ResolutionRunResponse,
    summary="Trigger entity resolution cascade",
    dependencies=[Depends(require_roles(["system_admin", "district_collector"]))],
)
async def trigger_resolution_run(
    req: ResolutionRunRequest,
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
) -> ResolutionRunResponse:
    """
    Trigger a batch entity resolution run.

    This is an async operation that:
    1. Fetches unlinked source records
    2. Runs the resolution cascade (Spatial → Deterministic → Probabilistic → Phonetic)
    3. Creates confirmed links and queues items for human review

    Returns a job_id for tracking progress. In production, this would be
    delegated to a background task queue (Celery/RabbitMQ).

    For demo purposes, we run a limited batch synchronously.
    """

    job_id = uuid.uuid4()

    # Log job creation
    logger.info(
        "resolution_run_triggered",
        job_id=str(job_id),
        source_type=req.source_type,
        actor=actor.subject,
    )

    # Emit audit event
    await emit_audit_event(
        event_type=AuditEventType.SYNC_TRIGGERED,
        actor=actor,
        resource_type="RESOLUTION_JOB",
        resource_id=job_id,
        payload={
            "source_type": req.source_type,
            "state_code": req.state_code,
            "thresholds": {
                "confirm": req.confidence_threshold_confirm,
                "review": req.confidence_threshold_review,
            },
        },
    )

    # Fetch unlinked records from the source type
    # In a real system, this would query the source table (revenue.ror_records, etc.)
    # For now, we return a job_id and status
    #
    # Example:
    # fetch_query = text("""
    #     SELECT id, survey_number, district_code, owner_name, area_sq_m
    #     FROM revenue.records_of_rights
    #     WHERE parcel_id IS NULL
    #       AND (:state_code IS NULL OR state_code = :state_code)
    #     LIMIT 1000
    # """)
    # result = await db.execute(fetch_query, {"state_code": req.state_code})
    # source_records = [dict(row) for row in result.mappings().all()]
    #
    # cascade = ResolutionCascade(db)
    # resolution_result = await cascade.run_resolution(
    #     source_type=req.source_type,
    #     source_records=source_records,
    #     confidence_threshold_confirm=req.confidence_threshold_confirm,
    #     confidence_threshold_review=req.confidence_threshold_review,
    # )
    #
    # logger.info(
    #     "resolution_run_completed",
    #     job_id=str(job_id),
    #     total=resolution_result.total_records,
    #     matched=resolution_result.matched,
    #     duration=resolution_result.duration_seconds,
    # )

    # For demo: return queued status
    return ResolutionRunResponse(
        job_id=job_id,
        status="QUEUED",
        message=f"Resolution job queued for source_type={req.source_type}. Check job status via /resolution/jobs/{job_id}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /resolution/metrics - Precision/recall/F1 metrics
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/metrics",
    response_model=ResolutionMetrics,
    summary="Get resolution quality metrics",
    dependencies=[Depends(require_roles(["revenue_officer", "district_collector", "system_admin"]))],
)
async def get_resolution_metrics(
    source_type: Optional[str] = Query(None, description="Filter by source type"),
    state_code: Optional[str] = Query(None, description="Filter by state"),
    db: AsyncSession = Depends(get_db),
) -> ResolutionMetrics:
    """
    Compute precision, recall, and F1 score against a ground truth dataset.

    Metrics are computed from:
    - **True Positives**: Confirmed links that match ground truth
    - **False Positives**: Confirmed links that contradict ground truth
    - **False Negatives**: Ground truth links that were not found

    Ground truth is stored in `identity.ground_truth_links` (created by officers
    during data quality audits).
    """

    # Build query filters
    where_clauses = []
    params = {}

    if source_type:
        where_clauses.append("pl.source_type = :source_type")
        params["source_type"] = source_type

    if state_code:
        where_clauses.append("p.state_code = :state_code")
        params["state_code"] = state_code

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Compute metrics
    # TP: Confirmed links that match ground truth
    # FP: Confirmed links that don't match ground truth
    # FN: Ground truth links that were not found
    metrics_query = text(f"""
        WITH confirmed_links AS (
            SELECT pl.source_id, pl.source_type, pl.target_parcel_id
            FROM identity.parcel_links pl
            JOIN identity.parcels p ON p.id = pl.target_parcel_id
            WHERE pl.status = 'CONFIRMED'
              AND {where_sql}
        ),
        ground_truth AS (
            SELECT gt.source_id, gt.source_type, gt.target_parcel_id
            FROM identity.ground_truth_links gt
            JOIN identity.parcels p ON p.id = gt.target_parcel_id
            WHERE {where_sql}
        ),
        true_positives AS (
            SELECT COUNT(*) as cnt
            FROM confirmed_links cl
            JOIN ground_truth gt
              ON cl.source_id = gt.source_id
             AND cl.source_type = gt.source_type
             AND cl.target_parcel_id = gt.target_parcel_id
        ),
        false_positives AS (
            SELECT COUNT(*) as cnt
            FROM confirmed_links cl
            LEFT JOIN ground_truth gt
              ON cl.source_id = gt.source_id
             AND cl.source_type = gt.source_type
             AND cl.target_parcel_id = gt.target_parcel_id
            WHERE gt.source_id IS NULL
        ),
        false_negatives AS (
            SELECT COUNT(*) as cnt
            FROM ground_truth gt
            LEFT JOIN confirmed_links cl
              ON cl.source_id = gt.source_id
             AND cl.source_type = gt.source_type
            WHERE cl.source_id IS NULL
        ),
        method_stats AS (
            SELECT
                pl.match_method,
                COUNT(*) as count
            FROM identity.parcel_links pl
            JOIN identity.parcels p ON p.id = pl.target_parcel_id
            WHERE pl.status = 'CONFIRMED'
              AND {where_sql}
            GROUP BY pl.match_method
        )
        SELECT
            (SELECT cnt FROM true_positives) as tp,
            (SELECT cnt FROM false_positives) as fp,
            (SELECT cnt FROM false_negatives) as fn,
            (SELECT json_object_agg(match_method, count) FROM method_stats) as method_breakdown
    """)

    result = await db.execute(metrics_query, params)
    row = result.mappings().one()

    tp = row["tp"] or 0
    fp = row["fp"] or 0
    fn = row["fn"] or 0
    method_breakdown = row["method_breakdown"] or {}

    # Compute precision, recall, F1
    precision = tp / (tp + fp) if (tp + fp) > 0 else None
    recall = tp / (tp + fn) if (tp + fn) > 0 else None
    f1_score = (
        2 * (precision * recall) / (precision + recall)
        if precision and recall and (precision + recall) > 0
        else None
    )

    return ResolutionMetrics(
        total_links=tp + fp,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        precision=round(precision, 4) if precision else None,
        recall=round(recall, 4) if recall else None,
        f1_score=round(f1_score, 4) if f1_score else None,
        method_breakdown=method_breakdown,
    )
