"""
Anomaly detection API endpoints.

Provides access to ML-detected anomalies with officer review capabilities.
"""

from __future__ import annotations

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from bhoomi_common.auth import Actor, get_current_actor, require_roles
from bhoomi_common.db import get_db
from app.modules.anomaly import (
    AnomalyScore,
    get_anomaly_score,
    run_anomaly_detection,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/anomalies", tags=["Anomalies"])

# ─────────────────────────────────────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────────────────────────────────────


class RescoreRequest(BaseModel):
    """Request to rescore anomalies."""
    state_code: Optional[str] = None
    district_code: Optional[str] = None
    contamination: float = 0.1


class AnomalySummary(BaseModel):
    """Summary statistics for anomalies."""
    total_anomalies: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    avg_anomaly_score: float
    top_anomaly_score: float


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/", response_model=List[AnomalyScore])
async def get_anomalies(
    state_code: Optional[str] = Query(None, description="Filter by state LGD code"),
    district_code: Optional[str] = Query(None, description="Filter by district LGD code"),
    min_score: float = Query(0.5, ge=0.0, le=1.0, description="Minimum anomaly score"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results to return"),
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    """
    Get ranked list of anomalies.

    Returns parcels with anomaly scores above the threshold, ranked by score (highest first).
    Officers see results filtered by their district scope.
    """
    logger.info(
        "get_anomalies",
        actor=actor.subject,
        state_code=state_code,
        district_code=district_code,
        min_score=min_score,
    )

    # Apply actor-level filtering
    if "revenue_officer" in actor.roles and actor.district_code:
        district_code = actor.district_code  # Override with actor's district

    # Build query
    from sqlalchemy import text

    filters = ["cs.score_type = 'ANOMALY'", "cs.is_latest = true", "cs.score_value >= :min_score"]
    params = {"min_score": min_score, "limit": limit}

    if state_code:
        filters.append("p.state_code = :state_code")
        params["state_code"] = state_code

    if district_code:
        filters.append("p.district_code = :district_code")
        params["district_code"] = district_code

    where_clause = " AND ".join(filters)

    query = text(f"""
        SELECT
            cs.parcel_id,
            p.bdpr,
            cs.score_value,
            cs.percentile_rank,
            cs.contributing_factors,
            cs.computed_at,
            cs.model_version
        FROM ml.conflict_scores cs
        INNER JOIN identity.parcels p ON cs.parcel_id = p.id
        WHERE {where_clause}
        ORDER BY cs.score_value DESC
        LIMIT :limit
    """)

    result = await db.execute(query, params)
    rows = result.fetchall()

    anomalies = []
    for row in rows:
        factors = row.contributing_factors or {}
        anomalies.append(AnomalyScore(
            parcel_id=UUID(str(row.parcel_id)),
            bdpr=row.bdpr,
            anomaly_score=float(row.score_value),
            percentile_rank=float(row.percentile_rank),
            top_features=factors.get("top_features", []),
            reason_text=factors.get("reason", "Anomaly detected"),
            confidence_score=factors.get("confidence", 0.0),
            model_version=str(row.model_version),
            computed_at=row.computed_at,
        ))

    logger.info("get_anomalies.complete", count=len(anomalies))
    return anomalies


@router.get("/{parcel_id}", response_model=AnomalyScore)
async def get_anomaly_by_parcel(
    parcel_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    """
    Get anomaly score for a specific parcel.

    Returns 404 if no anomaly score exists for the parcel.
    """
    logger.info("get_anomaly_by_parcel", parcel_id=str(parcel_id), actor=actor.subject)

    score = await get_anomaly_score(db, parcel_id)

    if score is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No anomaly score found for parcel {parcel_id}",
        )

    return score


@router.post("/rescore", status_code=status.HTTP_202_ACCEPTED)
async def rescore_anomalies(
    request: RescoreRequest,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(require_roles(["revenue_officer", "district_collector", "system_admin"])),
):
    """
    Trigger anomaly rescoring (officer-only).

    Re-runs the anomaly detection model with updated data.
    This is an async operation; results will be available after completion.
    """
    logger.info(
        "rescore_anomalies",
        actor=actor.subject,
        state_code=request.state_code,
        district_code=request.district_code,
    )

    # Officers can only rescore their own district
    if "revenue_officer" in actor.roles and actor.district_code:
        if request.district_code and request.district_code != actor.district_code:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Officers can only rescore their own district",
            )
        request.district_code = actor.district_code

    # Run anomaly detection
    try:
        results = await run_anomaly_detection(
            db,
            state_code=request.state_code,
            district_code=request.district_code,
            contamination=request.contamination,
            store_results=True,
        )

        return {
            "status": "completed",
            "message": f"Rescored {len(results)} parcels",
            "anomalies_detected": len([r for r in results if r.anomaly_score >= 0.5]),
        }

    except Exception as e:
        logger.error("rescore_anomalies: error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rescoring failed: {str(e)}",
        )


@router.get("/summary", response_model=AnomalySummary)
async def get_anomaly_summary(
    state_code: Optional[str] = Query(None),
    district_code: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    """
    Get summary statistics for anomalies.

    Returns aggregate counts and scores.
    """
    logger.info("get_anomaly_summary", actor=actor.subject)

    # Apply actor-level filtering
    if "revenue_officer" in actor.roles and actor.district_code:
        district_code = actor.district_code

    from sqlalchemy import text

    filters = ["cs.score_type = 'ANOMALY'", "cs.is_latest = true"]
    params = {}

    if state_code:
        filters.append("p.state_code = :state_code")
        params["state_code"] = state_code

    if district_code:
        filters.append("p.district_code = :district_code")
        params["district_code"] = district_code

    where_clause = " AND ".join(filters)

    query = text(f"""
        SELECT
            COUNT(*) AS total_count,
            SUM(CASE WHEN cs.risk_band = 'HIGH' THEN 1 ELSE 0 END) AS high_risk_count,
            SUM(CASE WHEN cs.risk_band = 'MEDIUM' THEN 1 ELSE 0 END) AS medium_risk_count,
            SUM(CASE WHEN cs.risk_band = 'LOW' THEN 1 ELSE 0 END) AS low_risk_count,
            AVG(cs.score_value) AS avg_score,
            MAX(cs.score_value) AS max_score
        FROM ml.conflict_scores cs
        INNER JOIN identity.parcels p ON cs.parcel_id = p.id
        WHERE {where_clause}
    """)

    result = await db.execute(query, params)
    row = result.fetchone()

    if not row or row.total_count == 0:
        return AnomalySummary(
            total_anomalies=0,
            high_risk_count=0,
            medium_risk_count=0,
            low_risk_count=0,
            avg_anomaly_score=0.0,
            top_anomaly_score=0.0,
        )

    return AnomalySummary(
        total_anomalies=int(row.total_count),
        high_risk_count=int(row.high_risk_count),
        medium_risk_count=int(row.medium_risk_count),
        low_risk_count=int(row.low_risk_count),
        avg_anomaly_score=round(float(row.avg_score), 4),
        top_anomaly_score=round(float(row.max_score), 4),
    )
