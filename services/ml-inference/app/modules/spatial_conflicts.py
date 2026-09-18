"""
Spatial conflict detection module - PostGIS-based deterministic checks.

Uses PostGIS topology functions to detect overlaps, gaps, slivers, area mismatches,
and encroachment on restricted zones. Never requires labeled training data.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Response Models
# ─────────────────────────────────────────────────────────────────────────────


class ConflictReport(BaseModel):
    """Report of a detected spatial conflict."""
    conflict_id: Optional[UUID] = None
    conflict_type: str
    severity: str  # HIGH | MEDIUM | LOW
    parcel_ids: List[UUID]
    description: str
    evidence: dict
    recommended_action: str
    detected_at: datetime
    detection_method: str = "AUTO"
    confidence_score: float = 1.0  # Deterministic checks = 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Overlap Detection
# ─────────────────────────────────────────────────────────────────────────────


async def detect_overlapping_parcels(
    db: AsyncSession,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    min_overlap_sq_m: float = 1.0,
) -> List[ConflictReport]:
    """
    Detect parcels with overlapping geometries using PostGIS ST_Intersection.

    Computes Intersection over Union (IoU) and flags overlaps greater than min_overlap_sq_m.

    Args:
        db: Database session
        state_code: Optional state filter (LGD code)
        district_code: Optional district filter (LGD code)
        min_overlap_sq_m: Minimum overlap area in square meters (default 1.0)

    Returns:
        List of ConflictReport with overlap details
    """
    logger.info(
        "detect_overlapping_parcels",
        state_code=state_code,
        district_code=district_code,
        min_overlap_sq_m=min_overlap_sq_m,
    )

    # Build spatial query with optional filters
    filters = []
    if state_code:
        filters.append(f"p1.state_code = :state_code AND p2.state_code = :state_code")
    if district_code:
        filters.append(f"p1.district_code = :district_code AND p2.district_code = :district_code")

    where_clause = f"AND {' AND '.join(filters)}" if filters else ""

    query = text(f"""
        WITH overlaps AS (
            SELECT
                p1.id AS parcel_id_1,
                p2.id AS parcel_id_2,
                p1.bdpr AS bdpr_1,
                p2.bdpr AS bdpr_2,
                ST_Area(ST_Intersection(g1.geometry, g2.geometry)::geography) AS overlap_area_sq_m,
                ST_Area(g1.geometry::geography) AS area_1,
                ST_Area(g2.geometry::geography) AS area_2,
                ST_AsText(ST_Intersection(g1.geometry, g2.geometry)) AS overlap_wkt
            FROM identity.parcels p1
            INNER JOIN geo.parcel_geometries g1 ON p1.id = g1.parcel_id AND g1.is_current = true
            INNER JOIN geo.parcel_geometries g2 ON g1.geometry && g2.geometry  -- Spatial index hint
            INNER JOIN identity.parcels p2 ON p2.id = g2.parcel_id
            WHERE p1.id < p2.id  -- Avoid duplicate pairs
                AND ST_Intersects(g1.geometry, g2.geometry)
                AND ST_Dimension(ST_Intersection(g1.geometry, g2.geometry)) = 2  -- Only polygons
                AND p1.is_active = true
                AND p2.is_active = true
                AND g2.is_current = true
                {where_clause}
        )
        SELECT * FROM overlaps
        WHERE overlap_area_sq_m >= :min_overlap_sq_m
        ORDER BY overlap_area_sq_m DESC
        LIMIT 500
    """)

    params = {"min_overlap_sq_m": min_overlap_sq_m}
    if state_code:
        params["state_code"] = state_code
    if district_code:
        params["district_code"] = district_code

    result = await db.execute(query, params)
    rows = result.fetchall()

    conflicts = []
    for row in rows:
        overlap_area = float(row.overlap_area_sq_m)
        area_1 = float(row.area_1)
        area_2 = float(row.area_2)

        # Compute IoU (Intersection over Union)
        union_area = area_1 + area_2 - overlap_area
        iou = overlap_area / union_area if union_area > 0 else 0

        # Determine severity
        if iou > 0.5 or overlap_area > 100:  # >50% overlap or >100 sq_m
            severity = "HIGH"
        elif overlap_area > 10:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        conflicts.append(ConflictReport(
            conflict_type="OVERLAP",
            severity=severity,
            parcel_ids=[UUID(str(row.parcel_id_1)), UUID(str(row.parcel_id_2))],
            description=f"Parcels {row.bdpr_1} and {row.bdpr_2} overlap by {overlap_area:.2f} sq_m (IoU: {iou:.3f})",
            evidence={
                "overlap_area_sq_m": round(overlap_area, 2),
                "iou": round(iou, 3),
                "parcel_1_area_sq_m": round(area_1, 2),
                "parcel_2_area_sq_m": round(area_2, 2),
                "overlap_geometry_wkt": str(row.overlap_wkt)[:500],  # Truncate
            },
            recommended_action="Review boundary survey records. If overlap is genuine, initiate dispute resolution. Check if parcels represent same real-world entity (requires entity resolution).",
            detected_at=datetime.utcnow(),
        ))

    logger.info("detect_overlapping_parcels.complete", count=len(conflicts))
    return conflicts


# ─────────────────────────────────────────────────────────────────────────────
# Gap and Sliver Detection
# ─────────────────────────────────────────────────────────────────────────────


async def detect_gaps_slivers(
    db: AsyncSession,
    state_code: str,
    district_code: Optional[str] = None,
    min_gap_area_sq_m: float = 5.0,
    max_gap_area_sq_m: float = 1000.0,
) -> List[ConflictReport]:
    """
    Detect void polygons (gaps/slivers) between parcels in a region.

    Computes the difference between the village boundary envelope and the union
    of all parcel geometries to find unmapped gaps.

    Args:
        db: Database session
        state_code: State LGD code (required for scoping)
        district_code: Optional district filter
        min_gap_area_sq_m: Minimum gap size to report (default 5 sq_m)
        max_gap_area_sq_m: Maximum gap size to report (default 1000 sq_m, above = roads/water)

    Returns:
        List of ConflictReport for detected gaps
    """
    logger.info(
        "detect_gaps_slivers",
        state_code=state_code,
        district_code=district_code,
    )

    # Note: This is a simplified approach. Production would use village-level analysis.
    # For demonstration, we'll detect gaps within a bounding box of parcels.

    district_filter = "AND p.district_code = :district_code" if district_code else ""

    query = text(f"""
        WITH parcel_union AS (
            SELECT ST_Union(g.geometry) AS union_geom
            FROM identity.parcels p
            INNER JOIN geo.parcel_geometries g ON p.id = g.parcel_id AND g.is_current = true
            WHERE p.state_code = :state_code
                AND p.is_active = true
                {district_filter}
            LIMIT 1000  -- Safety limit for union operation
        ),
        envelope AS (
            SELECT ST_ConvexHull(union_geom) AS hull_geom
            FROM parcel_union
        ),
        gaps AS (
            SELECT
                ST_Difference(e.hull_geom, pu.union_geom) AS gap_geom
            FROM envelope e
            CROSS JOIN parcel_union pu
            WHERE ST_Area(e.hull_geom::geography) > 0
        ),
        gap_polygons AS (
            SELECT
                (ST_Dump(gap_geom)).geom AS gap_poly,
                ST_Area((ST_Dump(gap_geom)).geom::geography) AS gap_area_sq_m
            FROM gaps
        )
        SELECT
            gap_poly,
            gap_area_sq_m,
            ST_AsText(ST_Centroid(gap_poly)) AS centroid_wkt
        FROM gap_polygons
        WHERE gap_area_sq_m BETWEEN :min_gap AND :max_gap
        ORDER BY gap_area_sq_m DESC
        LIMIT 100
    """)

    params = {
        "state_code": state_code,
        "min_gap": min_gap_area_sq_m,
        "max_gap": max_gap_area_sq_m,
    }
    if district_code:
        params["district_code"] = district_code

    result = await db.execute(query, params)
    rows = result.fetchall()

    conflicts = []
    for idx, row in enumerate(rows):
        gap_area = float(row.gap_area_sq_m)

        # Classify as gap or sliver based on shape
        if gap_area < 50:
            conflict_type = "SLIVER"
            severity = "LOW"
            action = "Likely survey artifact. Review for boundary adjustment or poramboke classification."
        else:
            conflict_type = "GAP"
            severity = "MEDIUM"
            action = "Unmapped area detected. Verify if this is a road, water body, or unregistered land."

        conflicts.append(ConflictReport(
            conflict_type=conflict_type,
            severity=severity,
            parcel_ids=[],  # No specific parcel, but adjacent parcels could be identified
            description=f"Void polygon of {gap_area:.2f} sq_m detected between registered parcels at {row.centroid_wkt}",
            evidence={
                "gap_area_sq_m": round(gap_area, 2),
                "centroid": str(row.centroid_wkt),
                "gap_index": idx,
            },
            recommended_action=action,
            detected_at=datetime.utcnow(),
        ))

    logger.info("detect_gaps_slivers.complete", count=len(conflicts))
    return conflicts


# ─────────────────────────────────────────────────────────────────────────────
# Area-Geometry Divergence
# ─────────────────────────────────────────────────────────────────────────────


async def detect_area_geometry_divergence(
    db: AsyncSession,
    parcel_id: Optional[UUID] = None,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    threshold_percent: float = 15.0,
) -> List[ConflictReport]:
    """
    Compare recorded area (from RoR) vs computed geometry area (ST_Area).

    Flags parcels where the divergence exceeds threshold_percent.

    Args:
        db: Database session
        parcel_id: Optional single parcel to check
        state_code: Optional state filter
        district_code: Optional district filter
        threshold_percent: Flag if divergence > this % (default 15%)

    Returns:
        List of ConflictReport for area mismatches
    """
    logger.info(
        "detect_area_geometry_divergence",
        parcel_id=parcel_id,
        state_code=state_code,
        threshold_percent=threshold_percent,
    )

    filters = []
    if parcel_id:
        filters.append("p.id = :parcel_id")
    if state_code:
        filters.append("p.state_code = :state_code")
    if district_code:
        filters.append("p.district_code = :district_code")

    where_clause = f"AND {' AND '.join(filters)}" if filters else ""

    query = text(f"""
        SELECT
            p.id AS parcel_id,
            p.bdpr,
            ror.area_sq_m AS recorded_area_sq_m,
            ST_Area(g.geometry::geography) AS computed_area_sq_m,
            ABS(ror.area_sq_m - ST_Area(g.geometry::geography)) AS divergence_abs,
            ABS(ror.area_sq_m - ST_Area(g.geometry::geography)) / NULLIF(ror.area_sq_m, 0) * 100 AS divergence_percent
        FROM identity.parcels p
        INNER JOIN geo.parcel_geometries g ON p.id = g.parcel_id AND g.is_current = true
        INNER JOIN revenue.records_of_rights ror ON p.id = ror.parcel_id AND ror.is_active = true
        WHERE p.is_active = true
            AND ror.area_sq_m IS NOT NULL
            AND ror.area_sq_m > 0
            {where_clause}
        HAVING ABS(ror.area_sq_m - ST_Area(g.geometry::geography)) / NULLIF(ror.area_sq_m, 0) * 100 > :threshold_percent
        ORDER BY divergence_percent DESC
        LIMIT 500
    """)

    params = {"threshold_percent": threshold_percent}
    if parcel_id:
        params["parcel_id"] = str(parcel_id)
    if state_code:
        params["state_code"] = state_code
    if district_code:
        params["district_code"] = district_code

    result = await db.execute(query, params)
    rows = result.fetchall()

    conflicts = []
    for row in rows:
        recorded = float(row.recorded_area_sq_m)
        computed = float(row.computed_area_sq_m)
        divergence_pct = float(row.divergence_percent)

        # Determine severity
        if divergence_pct > 50:
            severity = "HIGH"
        elif divergence_pct > 25:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        conflicts.append(ConflictReport(
            conflict_type="AREA_MISMATCH",
            severity=severity,
            parcel_ids=[UUID(str(row.parcel_id))],
            description=f"Parcel {row.bdpr}: recorded area {recorded:.2f} sq_m vs computed {computed:.2f} sq_m (divergence: {divergence_pct:.1f}%)",
            evidence={
                "recorded_area_sq_m": round(recorded, 2),
                "computed_area_sq_m": round(computed, 2),
                "divergence_sq_m": round(abs(recorded - computed), 2),
                "divergence_percent": round(divergence_pct, 1),
            },
            recommended_action="Verify RoR recorded area. If geometry is authoritative, update RoR. If RoR is correct, request resurvey.",
            detected_at=datetime.utcnow(),
        ))

    logger.info("detect_area_geometry_divergence.complete", count=len(conflicts))
    return conflicts


# ─────────────────────────────────────────────────────────────────────────────
# Encroachment on Restricted Zones
# ─────────────────────────────────────────────────────────────────────────────


async def detect_encroachment_on_restricted_zones(
    db: AsyncSession,
    parcel_id: Optional[UUID] = None,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    min_overlap_sq_m: float = 1.0,
) -> List[ConflictReport]:
    """
    Detect parcels overlapping with restricted zones (forest, water bodies, poramboke).

    Args:
        db: Database session
        parcel_id: Optional single parcel to check
        state_code: Optional state filter
        district_code: Optional district filter
        min_overlap_sq_m: Minimum overlap to flag (default 1 sq_m)

    Returns:
        List of ConflictReport for encroachments
    """
    logger.info(
        "detect_encroachment_on_restricted_zones",
        parcel_id=parcel_id,
        state_code=state_code,
    )

    filters = []
    if parcel_id:
        filters.append("p.id = :parcel_id")
    if state_code:
        filters.append("p.state_code = :state_code")
    if district_code:
        filters.append("p.district_code = :district_code")

    where_clause = f"AND {' AND '.join(filters)}" if filters else ""

    query = text(f"""
        SELECT
            p.id AS parcel_id,
            p.bdpr,
            rz.zone_type,
            rz.zone_name,
            ST_Area(ST_Intersection(g.geometry, rz.geometry)::geography) AS overlap_area_sq_m,
            ST_Area(g.geometry::geography) AS parcel_area_sq_m
        FROM identity.parcels p
        INNER JOIN geo.parcel_geometries g ON p.id = g.parcel_id AND g.is_current = true
        INNER JOIN geo.restricted_zones rz ON ST_Intersects(g.geometry, rz.geometry)
        WHERE p.is_active = true
            AND rz.is_active = true
            {where_clause}
            AND ST_Area(ST_Intersection(g.geometry, rz.geometry)::geography) >= :min_overlap_sq_m
        ORDER BY overlap_area_sq_m DESC
        LIMIT 500
    """)

    params = {"min_overlap_sq_m": min_overlap_sq_m}
    if parcel_id:
        params["parcel_id"] = str(parcel_id)
    if state_code:
        params["state_code"] = state_code
    if district_code:
        params["district_code"] = district_code

    result = await db.execute(query, params)
    rows = result.fetchall()

    conflicts = []
    for row in rows:
        overlap_area = float(row.overlap_area_sq_m)
        parcel_area = float(row.parcel_area_sq_m)
        overlap_pct = (overlap_area / parcel_area * 100) if parcel_area > 0 else 0

        # Determine severity
        if overlap_pct > 50 or overlap_area > 1000:
            severity = "HIGH"
        elif overlap_area > 100:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        zone_type = row.zone_type.upper()

        conflicts.append(ConflictReport(
            conflict_type=f"ENCROACHMENT_{zone_type}",
            severity=severity,
            parcel_ids=[UUID(str(row.parcel_id))],
            description=f"Parcel {row.bdpr} overlaps {row.zone_name} ({zone_type}) by {overlap_area:.2f} sq_m ({overlap_pct:.1f}% of parcel)",
            evidence={
                "zone_type": zone_type,
                "zone_name": str(row.zone_name),
                "overlap_area_sq_m": round(overlap_area, 2),
                "parcel_area_sq_m": round(parcel_area, 2),
                "overlap_percent": round(overlap_pct, 1),
            },
            recommended_action=f"Verify against {zone_type} department records. Check if parcel predates zone designation or if boundary error exists.",
            detected_at=datetime.utcnow(),
        ))

    logger.info("detect_encroachment_on_restricted_zones.complete", count=len(conflicts))
    return conflicts


# ─────────────────────────────────────────────────────────────────────────────
# Orchestration
# ─────────────────────────────────────────────────────────────────────────────


async def run_all_spatial_checks(
    db: AsyncSession,
    state_code: str,
    district_code: Optional[str] = None,
    parcel_id: Optional[UUID] = None,
) -> List[ConflictReport]:
    """
    Run all spatial conflict detection checks and return consolidated report.

    Args:
        db: Database session
        state_code: State LGD code (required)
        district_code: Optional district filter
        parcel_id: Optional single parcel to check (runs subset of checks)

    Returns:
        Consolidated list of all detected conflicts
    """
    logger.info(
        "run_all_spatial_checks.start",
        state_code=state_code,
        district_code=district_code,
        parcel_id=parcel_id,
    )

    all_conflicts = []

    # Run checks in parallel-capable sequence
    if parcel_id:
        # Single parcel mode: skip overlap/gap detection
        area_conflicts = await detect_area_geometry_divergence(
            db, parcel_id=parcel_id
        )
        encroachment_conflicts = await detect_encroachment_on_restricted_zones(
            db, parcel_id=parcel_id
        )
        all_conflicts.extend(area_conflicts)
        all_conflicts.extend(encroachment_conflicts)
    else:
        # Regional mode: run all checks
        overlap_conflicts = await detect_overlapping_parcels(
            db, state_code=state_code, district_code=district_code
        )
        gap_conflicts = await detect_gaps_slivers(
            db, state_code=state_code, district_code=district_code
        )
        area_conflicts = await detect_area_geometry_divergence(
            db, state_code=state_code, district_code=district_code
        )
        encroachment_conflicts = await detect_encroachment_on_restricted_zones(
            db, state_code=state_code, district_code=district_code
        )

        all_conflicts.extend(overlap_conflicts)
        all_conflicts.extend(gap_conflicts)
        all_conflicts.extend(area_conflicts)
        all_conflicts.extend(encroachment_conflicts)

    logger.info(
        "run_all_spatial_checks.complete",
        total_conflicts=len(all_conflicts),
        by_type={
            conflict_type: len([c for c in all_conflicts if c.conflict_type == conflict_type])
            for conflict_type in set(c.conflict_type for c in all_conflicts)
        },
    )

    return all_conflicts
