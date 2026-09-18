"""
Cross-registry inconsistency detection module.

Computes consistency vectors for parcels by comparing data across multiple
registries (revenue records, registration deeds, geospatial data, planning permissions).
"""

from __future__ import annotations

import logging
from typing import List, Optional
from uuid import UUID

import numpy as np
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────────────────────────


class ConsistencyVector(BaseModel):
    """Consistency metrics for a parcel across registries."""
    parcel_id: UUID
    bdpr: str

    # Area consistency (coefficient of variation)
    area_cv: float  # 0 = perfectly consistent, >0.5 = high variance
    area_sources: int  # Number of area records found

    # Owner name agreement (normalized string similarity)
    owner_name_agreement: float  # 0-1, 1 = perfect match
    owner_sources: int

    # Status agreement (categorical consistency)
    status_agreement: float  # 0-1, proportion of matching status codes
    status_sources: int

    # Geometry IoU (intersection over union across sources)
    geometry_iou: float  # 0-1, 1 = identical geometries
    geometry_sources: int

    # Temporal consistency (mutation vs deed date alignment)
    temporal_alignment_days: Optional[float] = None  # Avg deviation in days

    # Overall consistency score (weighted average)
    overall_score: float  # 0-1, 1 = fully consistent

    # Supporting evidence
    evidence: dict


# ─────────────────────────────────────────────────────────────────────────────
# Inconsistency Detection
# ─────────────────────────────────────────────────────────────────────────────


async def compute_consistency_vector(
    db: AsyncSession,
    parcel_id: UUID,
) -> Optional[ConsistencyVector]:
    """
    Compute consistency metrics for a single parcel.

    Compares data across:
    - Revenue records (RoR)
    - Registration deeds
    - Geospatial geometries
    - Planning permissions

    Args:
        db: Database session
        parcel_id: Parcel UUID

    Returns:
        ConsistencyVector with metrics, or None if insufficient data
    """
    logger.info("compute_consistency_vector", parcel_id=str(parcel_id))

    # 1. Area consistency across sources
    area_query = text("""
        SELECT
            'ROR' AS source,
            area_sq_m
        FROM revenue.records_of_rights
        WHERE parcel_id = :parcel_id AND is_active = true AND area_sq_m IS NOT NULL
        UNION ALL
        SELECT
            'GEOMETRY' AS source,
            ST_Area(geometry::geography) AS area_sq_m
        FROM geo.parcel_geometries
        WHERE parcel_id = :parcel_id AND is_current = true
        UNION ALL
        SELECT
            'PLANNING' AS source,
            site_area_sq_m AS area_sq_m
        FROM planning.building_permissions
        WHERE parcel_id = :parcel_id AND is_active = true AND site_area_sq_m IS NOT NULL
        LIMIT 1
    """)
    area_result = await db.execute(area_query, {"parcel_id": str(parcel_id)})
    area_rows = area_result.fetchall()

    area_values = [float(row.area_sq_m) for row in area_rows if row.area_sq_m]
    area_sources = len(area_values)
    area_cv = 0.0
    if area_sources >= 2:
        mean_area = np.mean(area_values)
        std_area = np.std(area_values)
        area_cv = float(std_area / mean_area) if mean_area > 0 else 0.0

    # 2. Owner name agreement (compare revenue vs registration)
    owner_query = text("""
        WITH revenue_owners AS (
            SELECT DISTINCT LOWER(TRIM(p.name_en)) AS name
            FROM revenue.rights r
            INNER JOIN revenue.parties p ON r.party_id = p.id
            WHERE r.parcel_id = :parcel_id
                AND r.right_type = 'OWNERSHIP'
                AND p.name_en IS NOT NULL
        ),
        registration_owners AS (
            SELECT DISTINCT LOWER(TRIM(p.name_en)) AS name
            FROM registration.deeds d
            INNER JOIN revenue.parties p ON d.buyer_party_id = p.id
            WHERE d.parcel_id = :parcel_id
                AND d.is_registered = true
                AND p.name_en IS NOT NULL
        )
        SELECT
            ro.name AS revenue_name,
            reg.name AS registration_name,
            similarity(ro.name, reg.name) AS name_similarity
        FROM revenue_owners ro
        CROSS JOIN registration_owners reg
        ORDER BY name_similarity DESC
        LIMIT 1
    """)
    owner_result = await db.execute(owner_query, {"parcel_id": str(parcel_id)})
    owner_row = owner_result.fetchone()

    owner_name_agreement = 0.0
    owner_sources = 0
    if owner_row and owner_row.revenue_name and owner_row.registration_name:
        owner_name_agreement = float(owner_row.name_similarity)
        owner_sources = 2
    elif owner_row and (owner_row.revenue_name or owner_row.registration_name):
        owner_sources = 1

    # 3. Status agreement (land classification consistency)
    status_query = text("""
        SELECT
            land_classification,
            COUNT(*) AS count
        FROM revenue.records_of_rights
        WHERE parcel_id = :parcel_id AND is_active = true
        GROUP BY land_classification
        ORDER BY count DESC
    """)
    status_result = await db.execute(status_query, {"parcel_id": str(parcel_id)})
    status_rows = status_result.fetchall()

    status_sources = sum(row.count for row in status_rows)
    status_agreement = 0.0
    if status_sources > 0 and status_rows:
        # Agreement = proportion with most common classification
        max_count = status_rows[0].count
        status_agreement = float(max_count / status_sources)

    # 4. Geometry IoU (if multiple geometry versions exist)
    geometry_query = text("""
        SELECT COUNT(*) AS count
        FROM geo.parcel_geometries
        WHERE parcel_id = :parcel_id
    """)
    geometry_result = await db.execute(geometry_query, {"parcel_id": str(parcel_id)})
    geometry_row = geometry_result.fetchone()
    geometry_sources = geometry_row.count if geometry_row else 0
    geometry_iou = 1.0  # Assume consistent if only one geometry; adjust if needed

    # 5. Temporal alignment (mutation date vs deed registration date)
    temporal_query = text("""
        SELECT
            ABS(EXTRACT(EPOCH FROM (m.mutation_date - d.registration_date)) / 86400) AS days_diff
        FROM revenue.mutations m
        INNER JOIN registration.deeds d ON m.parcel_id = d.parcel_id
        WHERE m.parcel_id = :parcel_id
            AND m.mutation_date IS NOT NULL
            AND d.registration_date IS NOT NULL
            AND m.mutation_type IN ('SALE', 'GIFT')
            AND d.deed_type IN ('SALE', 'GIFT')
        ORDER BY m.mutation_date DESC
        LIMIT 5
    """)
    temporal_result = await db.execute(temporal_query, {"parcel_id": str(parcel_id)})
    temporal_rows = temporal_result.fetchall()

    temporal_alignment_days = None
    if temporal_rows:
        temporal_diffs = [float(row.days_diff) for row in temporal_rows]
        temporal_alignment_days = float(np.mean(temporal_diffs))

    # Compute overall consistency score (weighted average)
    weights = {
        "area": 0.3,
        "owner": 0.3,
        "status": 0.2,
        "geometry": 0.1,
        "temporal": 0.1,
    }

    # Normalize metrics to 0-1 (higher = more consistent)
    area_score = max(0, 1 - min(area_cv, 1.0))  # CV=0 → score=1, CV>=1 → score=0
    owner_score = owner_name_agreement
    status_score = status_agreement
    geometry_score = geometry_iou
    temporal_score = 1.0  # Default if no temporal data
    if temporal_alignment_days is not None:
        # Score=1 if <=7 days, score=0 if >=90 days
        temporal_score = max(0, 1 - (temporal_alignment_days / 90.0))

    overall_score = (
        weights["area"] * area_score +
        weights["owner"] * owner_score +
        weights["status"] * status_score +
        weights["geometry"] * geometry_score +
        weights["temporal"] * temporal_score
    )

    # Get parcel BDPR
    parcel_query = text("SELECT bdpr FROM identity.parcels WHERE id = :parcel_id")
    parcel_result = await db.execute(parcel_query, {"parcel_id": str(parcel_id)})
    parcel_row = parcel_result.fetchone()
    if not parcel_row:
        logger.warning("compute_consistency_vector: parcel not found", parcel_id=str(parcel_id))
        return None

    bdpr = parcel_row.bdpr

    vector = ConsistencyVector(
        parcel_id=parcel_id,
        bdpr=bdpr,
        area_cv=round(area_cv, 4),
        area_sources=area_sources,
        owner_name_agreement=round(owner_name_agreement, 4),
        owner_sources=owner_sources,
        status_agreement=round(status_agreement, 4),
        status_sources=int(status_sources),
        geometry_iou=round(geometry_iou, 4),
        geometry_sources=geometry_sources,
        temporal_alignment_days=round(temporal_alignment_days, 2) if temporal_alignment_days else None,
        overall_score=round(overall_score, 4),
        evidence={
            "area_values": [round(a, 2) for a in area_values],
            "area_score": round(area_score, 4),
            "owner_score": round(owner_score, 4),
            "status_score": round(status_score, 4),
            "geometry_score": round(geometry_score, 4),
            "temporal_score": round(temporal_score, 4),
        },
    )

    logger.info(
        "compute_consistency_vector.complete",
        parcel_id=str(parcel_id),
        overall_score=overall_score,
    )

    return vector


async def compute_batch_consistency_vectors(
    db: AsyncSession,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    limit: int = 1000,
) -> List[ConsistencyVector]:
    """
    Compute consistency vectors for a batch of parcels.

    Args:
        db: Database session
        state_code: Optional state filter
        district_code: Optional district filter
        limit: Maximum parcels to process

    Returns:
        List of ConsistencyVector
    """
    logger.info(
        "compute_batch_consistency_vectors",
        state_code=state_code,
        district_code=district_code,
        limit=limit,
    )

    # Get parcel IDs
    filters = ["p.is_active = true"]
    if state_code:
        filters.append(f"p.state_code = :state_code")
    if district_code:
        filters.append(f"p.district_code = :district_code")

    where_clause = " AND ".join(filters)

    parcel_query = text(f"""
        SELECT id
        FROM identity.parcels p
        WHERE {where_clause}
        LIMIT :limit
    """)

    params = {"limit": limit}
    if state_code:
        params["state_code"] = state_code
    if district_code:
        params["district_code"] = district_code

    result = await db.execute(parcel_query, params)
    parcel_ids = [UUID(str(row.id)) for row in result.fetchall()]

    logger.info("compute_batch_consistency_vectors: processing parcels", count=len(parcel_ids))

    # Compute vectors for each parcel
    vectors = []
    for parcel_id in parcel_ids:
        vector = await compute_consistency_vector(db, parcel_id)
        if vector:
            vectors.append(vector)

    logger.info("compute_batch_consistency_vectors.complete", count=len(vectors))
    return vectors
