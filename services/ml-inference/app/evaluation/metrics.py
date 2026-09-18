"""
ML evaluation metrics module.

Computes evaluation metrics for spatial conflict detection, anomaly detection,
and graph network analysis.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────────────────────────


class MetricsReport(BaseModel):
    """Comprehensive evaluation metrics report."""
    report_timestamp: datetime
    model_version: str

    # Spatial conflict metrics
    spatial_conflict_metrics: Dict[str, float]

    # Anomaly detection metrics
    anomaly_detection_metrics: Dict[str, float]

    # Graph analysis metrics
    graph_analysis_metrics: Dict[str, float]

    # Overall summary
    overall_summary: Dict[str, any]


# ─────────────────────────────────────────────────────────────────────────────
# Spatial Conflict Metrics
# ─────────────────────────────────────────────────────────────────────────────


async def compute_spatial_conflict_recall(
    db: AsyncSession,
) -> Dict[str, float]:
    """
    Compute recall for spatial conflict detection.

    Recall = TP / (TP + FN)
    Where TP = conflicts detected and confirmed
          FN = conflicts missed (reported by external source but not detected)

    Since spatial checks are deterministic, recall should be near 100%
    for geometric conflicts. We measure against ground truth conflicts.

    Returns:
        Dict with recall metrics
    """
    logger.info("compute_spatial_conflict_recall")

    # Query detected conflicts (all auto-detected)
    detected_query = text("""
        SELECT
            COUNT(*) AS detected_count,
            SUM(CASE WHEN resolution_status IN ('RESOLVED', 'ACCEPTED_AS_IS') THEN 1 ELSE 0 END) AS confirmed_count
        FROM geo.topology_conflicts
        WHERE detection_method = 'AUTO'
            AND detected_at >= CURRENT_DATE - INTERVAL '30 days'
    """)

    result = await db.execute(detected_query)
    row = result.fetchone()

    detected_count = row.detected_count if row else 0
    confirmed_count = row.confirmed_count if row else 0

    # Query ground truth (manually reported conflicts)
    ground_truth_query = text("""
        SELECT COUNT(*) AS manual_count
        FROM geo.topology_conflicts
        WHERE detection_method = 'MANUAL'
            AND detected_at >= CURRENT_DATE - INTERVAL '30 days'
    """)

    gt_result = await db.execute(ground_truth_query)
    gt_row = gt_result.fetchone()

    manual_count = gt_row.manual_count if gt_row else 0

    # Compute recall (assuming manual conflicts are the "missed" ones)
    # This is a simplification; real ground truth would come from surveyed data
    total_true_conflicts = detected_count + manual_count
    recall = detected_count / total_true_conflicts if total_true_conflicts > 0 else 0.0

    # Precision: proportion of detected conflicts that are real
    precision = confirmed_count / detected_count if detected_count > 0 else 0.0

    metrics = {
        "recall": round(recall, 4),
        "precision": round(precision, 4),
        "detected_count": detected_count,
        "confirmed_count": confirmed_count,
        "manual_reported_count": manual_count,
        "f1_score": round(2 * (precision * recall) / (precision + recall), 4) if (precision + recall) > 0 else 0.0,
    }

    logger.info("compute_spatial_conflict_recall.complete", metrics=metrics)
    return metrics


# ─────────────────────────────────────────────────────────────────────────────
# Anomaly Detection Metrics
# ─────────────────────────────────────────────────────────────────────────────


async def compute_anomaly_precision_at_k(
    db: AsyncSession,
    k: int = 50,
) -> Dict[str, float]:
    """
    Compute precision@K for anomaly detection.

    Precision@K = Number of true positives in top K / K

    A "true positive" is an anomaly that was flagged and later
    confirmed by an officer (reviewed_status = CONFIRMED_SUSPICIOUS).

    Args:
        db: Database session
        k: Top-K to evaluate (default 50)

    Returns:
        Dict with precision@K metrics
    """
    logger.info("compute_anomaly_precision_at_k", k=k)

    # Get top K anomalies by score
    query = text("""
        WITH top_anomalies AS (
            SELECT
                cs.parcel_id,
                cs.score_value,
                cs.percentile_rank
            FROM ml.conflict_scores cs
            WHERE cs.score_type = 'ANOMALY'
                AND cs.is_latest = true
            ORDER BY cs.score_value DESC
            LIMIT :k
        )
        SELECT
            COUNT(*) AS top_k_count,
            -- Check if any have been confirmed via network flags or manual review
            -- (This is a proxy; real ground truth would come from officer review)
            SUM(CASE
                WHEN EXISTS (
                    SELECT 1 FROM ml.transaction_network_flags tnf
                    WHERE ta.parcel_id = ANY(tnf.parcel_ids)
                        AND tnf.reviewed_status = 'CONFIRMED_SUSPICIOUS'
                ) THEN 1
                ELSE 0
            END) AS confirmed_count
        FROM top_anomalies ta
    """)

    result = await db.execute(query, {"k": k})
    row = result.fetchone()

    top_k_count = row.top_k_count if row else 0
    confirmed_count = row.confirmed_count if row else 0

    precision_at_k = confirmed_count / k if k > 0 else 0.0

    # Also compute average score of top K
    avg_score_query = text("""
        SELECT AVG(score_value) AS avg_score
        FROM ml.conflict_scores
        WHERE score_type = 'ANOMALY'
            AND is_latest = true
        ORDER BY score_value DESC
        LIMIT :k
    """)

    avg_result = await db.execute(avg_score_query, {"k": k})
    avg_row = avg_result.fetchone()
    avg_score = float(avg_row.avg_score) if avg_row and avg_row.avg_score else 0.0

    metrics = {
        f"precision_at_{k}": round(precision_at_k, 4),
        "top_k_count": top_k_count,
        "confirmed_in_top_k": confirmed_count,
        "avg_score_top_k": round(avg_score, 4),
    }

    logger.info("compute_anomaly_precision_at_k.complete", metrics=metrics)
    return metrics


# ─────────────────────────────────────────────────────────────────────────────
# Graph Analysis Metrics
# ─────────────────────────────────────────────────────────────────────────────


async def compute_graph_circular_chain_recall(
    db: AsyncSession,
) -> Dict[str, float]:
    """
    Compute recall for circular chain detection.

    Recall = Detected chains / Known ground truth chains

    Ground truth comes from officer-confirmed suspicious patterns.

    Returns:
        Dict with recall metrics
    """
    logger.info("compute_graph_circular_chain_recall")

    # Detected circular chains
    detected_query = text("""
        SELECT COUNT(*) AS detected_count
        FROM ml.transaction_network_flags
        WHERE flag_type = 'CIRCULAR_CHAIN'
            AND detected_at >= CURRENT_DATE - INTERVAL '90 days'
    """)

    result = await db.execute(detected_query)
    row = result.fetchone()
    detected_count = row.detected_count if row else 0

    # Confirmed chains (officer reviewed)
    confirmed_query = text("""
        SELECT COUNT(*) AS confirmed_count
        FROM ml.transaction_network_flags
        WHERE flag_type = 'CIRCULAR_CHAIN'
            AND reviewed_status = 'CONFIRMED_SUSPICIOUS'
            AND detected_at >= CURRENT_DATE - INTERVAL '90 days'
    """)

    conf_result = await db.execute(confirmed_query)
    conf_row = conf_result.fetchone()
    confirmed_count = conf_row.confirmed_count if conf_row else 0

    # False positives
    false_positive_query = text("""
        SELECT COUNT(*) AS false_positive_count
        FROM ml.transaction_network_flags
        WHERE flag_type = 'CIRCULAR_CHAIN'
            AND reviewed_status = 'FALSE_POSITIVE'
            AND detected_at >= CURRENT_DATE - INTERVAL '90 days'
    """)

    fp_result = await db.execute(false_positive_query)
    fp_row = fp_result.fetchone()
    false_positive_count = fp_row.false_positive_count if fp_row else 0

    # Precision
    precision = confirmed_count / detected_count if detected_count > 0 else 0.0

    # Recall (assuming confirmed + some undetected = ground truth)
    # This is a proxy metric; real recall needs external ground truth
    recall_estimate = confirmed_count / (confirmed_count + 1) if confirmed_count > 0 else 0.0

    metrics = {
        "circular_chains_detected": detected_count,
        "circular_chains_confirmed": confirmed_count,
        "circular_chains_false_positive": false_positive_count,
        "precision": round(precision, 4),
        "recall_estimate": round(recall_estimate, 4),
    }

    logger.info("compute_graph_circular_chain_recall.complete", metrics=metrics)
    return metrics


async def compute_graph_rapid_flip_metrics(
    db: AsyncSession,
) -> Dict[str, float]:
    """
    Compute metrics for rapid flip detection.

    Returns:
        Dict with rapid flip metrics
    """
    logger.info("compute_graph_rapid_flip_metrics")

    # Detected rapid flips
    detected_query = text("""
        SELECT COUNT(*) AS detected_count
        FROM ml.transaction_network_flags
        WHERE flag_type = 'RAPID_FLIP'
            AND detected_at >= CURRENT_DATE - INTERVAL '90 days'
    """)

    result = await db.execute(detected_query)
    row = result.fetchone()
    detected_count = row.detected_count if row else 0

    # Confirmed
    confirmed_query = text("""
        SELECT COUNT(*) AS confirmed_count
        FROM ml.transaction_network_flags
        WHERE flag_type = 'RAPID_FLIP'
            AND reviewed_status = 'CONFIRMED_SUSPICIOUS'
            AND detected_at >= CURRENT_DATE - INTERVAL '90 days'
    """)

    conf_result = await db.execute(confirmed_query)
    conf_row = conf_result.fetchone()
    confirmed_count = conf_row.confirmed_count if conf_row else 0

    precision = confirmed_count / detected_count if detected_count > 0 else 0.0

    metrics = {
        "rapid_flips_detected": detected_count,
        "rapid_flips_confirmed": confirmed_count,
        "precision": round(precision, 4),
    }

    logger.info("compute_graph_rapid_flip_metrics.complete", metrics=metrics)
    return metrics


# ─────────────────────────────────────────────────────────────────────────────
# Overall Metrics Computation
# ─────────────────────────────────────────────────────────────────────────────


async def compute_all_metrics(
    db: AsyncSession,
    model_version: str = "v1.0",
) -> MetricsReport:
    """
    Compute all evaluation metrics across modules.

    Args:
        db: Database session
        model_version: Model version string

    Returns:
        MetricsReport with comprehensive metrics
    """
    logger.info("compute_all_metrics.start", model_version=model_version)

    # 1. Spatial conflict metrics
    spatial_metrics = await compute_spatial_conflict_recall(db)

    # 2. Anomaly detection metrics
    anomaly_metrics_50 = await compute_anomaly_precision_at_k(db, k=50)
    anomaly_metrics_100 = await compute_anomaly_precision_at_k(db, k=100)

    anomaly_metrics = {
        **anomaly_metrics_50,
        **{f"{k}_at_100": v for k, v in anomaly_metrics_100.items()},
    }

    # 3. Graph analysis metrics
    circular_chain_metrics = await compute_graph_circular_chain_recall(db)
    rapid_flip_metrics = await compute_graph_rapid_flip_metrics(db)

    graph_metrics = {
        **circular_chain_metrics,
        **rapid_flip_metrics,
    }

    # 4. Overall summary
    overall_summary = {
        "spatial_precision": spatial_metrics.get("precision", 0.0),
        "spatial_recall": spatial_metrics.get("recall", 0.0),
        "anomaly_precision_at_50": anomaly_metrics.get("precision_at_50", 0.0),
        "graph_circular_precision": graph_metrics.get("precision", 0.0),
        "total_conflicts_detected": spatial_metrics.get("detected_count", 0),
        "total_anomalies_flagged": anomaly_metrics.get("top_k_count", 0),
        "total_circular_chains": graph_metrics.get("circular_chains_detected", 0),
    }

    report = MetricsReport(
        report_timestamp=datetime.utcnow(),
        model_version=model_version,
        spatial_conflict_metrics=spatial_metrics,
        anomaly_detection_metrics=anomaly_metrics,
        graph_analysis_metrics=graph_metrics,
        overall_summary=overall_summary,
    )

    logger.info("compute_all_metrics.complete", model_version=model_version)
    return report
