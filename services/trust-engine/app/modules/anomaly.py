"""
Unsupervised anomaly detection using Isolation Forest.

Runs anomaly detection over consistency vectors to surface parcels
with unusual patterns that warrant officer review.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

import numpy as np
import pandas as pd
from pydantic import BaseModel
from scipy import stats
from sklearn.ensemble import IsolationForest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inconsistency import ConsistencyVector, compute_batch_consistency_vectors

logger = logging.getLogger(__name__)

MODEL_VERSION = "isolation_forest_v1.0"

# ─────────────────────────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────────────────────────


class AnomalyScore(BaseModel):
    """Anomaly score for a parcel."""
    parcel_id: UUID
    bdpr: str
    anomaly_score: float  # 0-1, higher = more anomalous
    percentile_rank: float  # 0-100
    top_features: List[str]  # Features contributing most to anomaly
    reason_text: str  # Human-readable explanation
    confidence_score: float  # Model confidence (based on consistency of predictions)
    model_version: str
    computed_at: datetime
    is_latest: bool = True


# ─────────────────────────────────────────────────────────────────────────────
# Anomaly Detection
# ─────────────────────────────────────────────────────────────────────────────


def _prepare_feature_matrix(vectors: List[ConsistencyVector]) -> pd.DataFrame:
    """Convert consistency vectors to feature matrix for ML."""
    data = []
    for v in vectors:
        data.append({
            "parcel_id": str(v.parcel_id),
            "bdpr": v.bdpr,
            "area_cv": v.area_cv,
            "owner_name_agreement": v.owner_name_agreement,
            "status_agreement": v.status_agreement,
            "geometry_iou": v.geometry_iou,
            "temporal_alignment_days": v.temporal_alignment_days or 0.0,
            "overall_score": v.overall_score,
            "area_sources": v.area_sources,
            "owner_sources": v.owner_sources,
        })

    df = pd.DataFrame(data)
    return df


def _generate_reason_text(
    row: pd.Series,
    feature_importances: dict,
    top_n: int = 3,
) -> tuple[List[str], str]:
    """
    Generate human-readable explanation for anomaly score.

    Returns:
        (top_features, reason_text)
    """
    # Get top contributing features
    top_features = sorted(
        feature_importances.items(),
        key=lambda x: abs(x[1]),
        reverse=True,
    )[:top_n]

    reasons = []
    feature_names = []

    for feature, importance in top_features:
        feature_names.append(feature)
        value = row[feature]

        if feature == "area_cv" and value > 0.3:
            reasons.append(f"High area variation across registries (CV={value:.2f})")
        elif feature == "owner_name_agreement" and value < 0.6:
            reasons.append(f"Low owner name agreement ({value:.1%})")
        elif feature == "status_agreement" and value < 0.7:
            reasons.append(f"Inconsistent land classification ({value:.1%} agreement)")
        elif feature == "temporal_alignment_days" and value > 30:
            reasons.append(f"Large time gap between mutation and deed ({value:.0f} days)")
        elif feature == "overall_score" and value < 0.5:
            reasons.append(f"Low overall consistency score ({value:.1%})")
        else:
            reasons.append(f"Unusual {feature.replace('_', ' ')}: {value:.2f}")

    if not reasons:
        reasons.append("Multiple minor inconsistencies detected")

    reason_text = "Anomaly surfaced for review: " + "; ".join(reasons)
    return feature_names, reason_text


async def run_anomaly_detection(
    db: AsyncSession,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    contamination: float = 0.1,
    store_results: bool = True,
) -> List[AnomalyScore]:
    """
    Run Isolation Forest anomaly detection over parcel consistency vectors.

    Args:
        db: Database session
        state_code: Optional state filter
        district_code: Optional district filter
        contamination: Expected proportion of anomalies (default 0.1 = 10%)
        store_results: Whether to persist results to ml.conflict_scores table

    Returns:
        List of AnomalyScore, ranked by anomaly score (highest first)
    """
    logger.info(
        "run_anomaly_detection.start",
        state_code=state_code,
        district_code=district_code,
        contamination=contamination,
    )

    # 1. Compute consistency vectors
    vectors = await compute_batch_consistency_vectors(
        db,
        state_code=state_code,
        district_code=district_code,
        limit=5000,  # Process in batches
    )

    if len(vectors) < 10:
        logger.warning("run_anomaly_detection: insufficient data", count=len(vectors))
        return []

    # 2. Prepare feature matrix
    df = _prepare_feature_matrix(vectors)

    # Feature columns for anomaly detection
    feature_cols = [
        "area_cv",
        "owner_name_agreement",
        "status_agreement",
        "geometry_iou",
        "temporal_alignment_days",
        "overall_score",
    ]

    X = df[feature_cols].fillna(0).values

    # 3. Run Isolation Forest
    logger.info("run_anomaly_detection: training IsolationForest", n_samples=len(X))

    iso_forest = IsolationForest(
        contamination=contamination,
        random_state=42,
        n_estimators=100,
        max_samples="auto",
        bootstrap=False,
    )

    # Fit and predict
    anomaly_labels = iso_forest.fit_predict(X)  # -1 = anomaly, 1 = normal
    anomaly_scores_raw = iso_forest.score_samples(X)  # Lower = more anomalous

    # Normalize scores to 0-1 range (higher = more anomalous)
    # Isolation Forest returns negative scores, so invert
    anomaly_scores_normalized = 1 - (
        (anomaly_scores_raw - anomaly_scores_raw.min()) /
        (anomaly_scores_raw.max() - anomaly_scores_raw.min())
    )

    df["anomaly_score"] = anomaly_scores_normalized
    df["is_anomaly"] = (anomaly_labels == -1)

    # 4. Compute Z-scores as secondary signal
    z_scores = np.abs(stats.zscore(X, axis=0))
    df["max_z_score"] = z_scores.max(axis=1)

    # 5. Compute percentile ranks
    df["percentile_rank"] = df["anomaly_score"].rank(pct=True) * 100

    # 6. Feature importance (approximate via feature deviation)
    feature_importances = {}
    for i, col in enumerate(feature_cols):
        # Higher z-score mean = more important for anomaly
        feature_importances[col] = float(z_scores[:, i].mean())

    # 7. Generate explanations and create AnomalyScore objects
    anomaly_results = []

    for idx, row in df.iterrows():
        top_features, reason_text = _generate_reason_text(
            row,
            feature_importances,
            top_n=3,
        )

        # Confidence: higher if multiple features are anomalous
        confidence = min(1.0, row["max_z_score"] / 3.0)  # Z>3 = high confidence

        anomaly_results.append(AnomalyScore(
            parcel_id=UUID(row["parcel_id"]),
            bdpr=row["bdpr"],
            anomaly_score=round(float(row["anomaly_score"]), 4),
            percentile_rank=round(float(row["percentile_rank"]), 2),
            top_features=top_features,
            reason_text=reason_text,
            confidence_score=round(float(confidence), 4),
            model_version=MODEL_VERSION,
            computed_at=datetime.utcnow(),
        ))

    # Sort by anomaly score descending
    anomaly_results.sort(key=lambda x: x.anomaly_score, reverse=True)

    logger.info(
        "run_anomaly_detection.complete",
        total_processed=len(vectors),
        anomalies_detected=sum(df["is_anomaly"]),
        top_score=anomaly_results[0].anomaly_score if anomaly_results else 0,
    )

    # 8. Store results in database
    if store_results and anomaly_results:
        await _store_anomaly_scores(db, anomaly_results)

    return anomaly_results


async def _store_anomaly_scores(
    db: AsyncSession,
    scores: List[AnomalyScore],
) -> None:
    """Persist anomaly scores to ml.conflict_scores table."""
    logger.info("_store_anomaly_scores", count=len(scores))

    # Mark previous scores as not latest
    update_query = text("""
        UPDATE ml.conflict_scores
        SET is_latest = false
        WHERE score_type = 'ANOMALY'
            AND model_version = :model_version
            AND is_latest = true
    """)
    await db.execute(update_query, {"model_version": MODEL_VERSION})

    # Insert new scores
    insert_query = text("""
        INSERT INTO ml.conflict_scores (
            parcel_id,
            score_type,
            score_value,
            risk_band,
            percentile_rank,
            method,
            contributing_factors,
            computed_at,
            model_version,
            is_latest
        ) VALUES (
            :parcel_id,
            'ANOMALY',
            :score_value,
            :risk_band,
            :percentile_rank,
            'isolation_forest',
            :contributing_factors,
            :computed_at,
            :model_version,
            true
        )
        ON CONFLICT (parcel_id, score_type, model_version)
        DO UPDATE SET
            score_value = EXCLUDED.score_value,
            risk_band = EXCLUDED.risk_band,
            percentile_rank = EXCLUDED.percentile_rank,
            contributing_factors = EXCLUDED.contributing_factors,
            computed_at = EXCLUDED.computed_at,
            is_latest = true
    """)

    for score in scores:
        # Determine risk band
        if score.anomaly_score >= 0.8:
            risk_band = "HIGH"
        elif score.anomaly_score >= 0.6:
            risk_band = "MEDIUM"
        elif score.anomaly_score >= 0.4:
            risk_band = "LOW"
        else:
            risk_band = "NEGLIGIBLE"

        contributing_factors = {
            "top_features": score.top_features,
            "reason": score.reason_text,
            "confidence": score.confidence_score,
        }

        await db.execute(insert_query, {
            "parcel_id": str(score.parcel_id),
            "score_value": score.anomaly_score,
            "risk_band": risk_band,
            "percentile_rank": score.percentile_rank,
            "contributing_factors": contributing_factors,
            "computed_at": score.computed_at,
            "model_version": MODEL_VERSION,
        })

    await db.commit()
    logger.info("_store_anomaly_scores.complete")


async def get_anomaly_score(
    db: AsyncSession,
    parcel_id: UUID,
) -> Optional[AnomalyScore]:
    """Retrieve the latest anomaly score for a parcel."""
    query = text("""
        SELECT
            parcel_id,
            score_value,
            percentile_rank,
            contributing_factors,
            computed_at,
            model_version
        FROM ml.conflict_scores
        WHERE parcel_id = :parcel_id
            AND score_type = 'ANOMALY'
            AND is_latest = true
    """)

    result = await db.execute(query, {"parcel_id": str(parcel_id)})
    row = result.fetchone()

    if not row:
        return None

    # Get BDPR
    parcel_query = text("SELECT bdpr FROM identity.parcels WHERE id = :parcel_id")
    parcel_result = await db.execute(parcel_query, {"parcel_id": str(parcel_id)})
    parcel_row = parcel_result.fetchone()
    bdpr = parcel_row.bdpr if parcel_row else "UNKNOWN"

    factors = row.contributing_factors or {}

    return AnomalyScore(
        parcel_id=UUID(str(row.parcel_id)),
        bdpr=bdpr,
        anomaly_score=float(row.score_value),
        percentile_rank=float(row.percentile_rank),
        top_features=factors.get("top_features", []),
        reason_text=factors.get("reason", "Anomaly detected"),
        confidence_score=factors.get("confidence", 0.0),
        model_version=str(row.model_version),
        computed_at=row.computed_at,
    )
