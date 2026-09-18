"""
Spatial query endpoints: within-polygon, nearby-point, conflict listing,
and on-demand topology conflict detection.

All heavy lifting (geometry intersection, distance ordering, overlap
computation) runs inside PostGIS.  Python receives lightweight result sets.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.geo import (
    ConflictDetectionResponse,
    ConflictListResponse,
    DetectedOverlap,
    NearbyQueryRequest,
    ParcelSpatialResult,
    SpatialQueryResponse,
    TopologyConflictResponse,
    WithinQueryRequest,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/geo", tags=["Spatial Queries"])


# ---------------------------------------------------------------------------
# POST /api/v1/geo/query/within
# ---------------------------------------------------------------------------

@router.post(
    "/query/within",
    response_model=SpatialQueryResponse,
    summary="Find parcels within a GeoJSON Polygon",
)
async def query_within(
    body: WithinQueryRequest,
    db: AsyncSession = Depends(get_db),
) -> SpatialQueryResponse:
    """
    Return all parcels whose centroid is within (or whose boundary intersects)
    the supplied GeoJSON Polygon.

    The polygon must be in WGS84 (EPSG:4326), anti-clockwise winding order.

    Results are ordered by BDPR.
    """
    geojson_str = json.dumps({"type": body.type, "coordinates": body.coordinates})

    result = await db.execute(
        text(
            """
            SELECT
                g.parcel_id,
                p.bdpr,
                p.ulpin,
                p.state_code,
                p.district_code,
                p.is_urban,
                g.area_sq_m,
                g.accuracy_class
            FROM geo.parcel_geometries g
            JOIN identity.parcels p
              ON p.id = g.parcel_id
            WHERE g.is_active = true
              AND p.is_active = true
              AND (
                    ST_Within(ST_Centroid(g.geometry), ST_GeomFromGeoJSON(:geojson))
                 OR ST_Intersects(g.geometry,           ST_GeomFromGeoJSON(:geojson))
              )
            ORDER BY p.bdpr
            """
        ),
        {"geojson": geojson_str},
    )
    rows = result.mappings().all()

    items = [
        ParcelSpatialResult(
            parcel_id=r["parcel_id"],
            bdpr=r["bdpr"],
            ulpin=r["ulpin"],
            state_code=r["state_code"],
            district_code=r["district_code"],
            is_urban=r["is_urban"],
            area_sq_m=float(r["area_sq_m"]) if r["area_sq_m"] is not None else None,
            accuracy_class=r["accuracy_class"],
        )
        for r in rows
    ]
    return SpatialQueryResponse(items=items, count=len(items))


# ---------------------------------------------------------------------------
# POST /api/v1/geo/query/nearby
# ---------------------------------------------------------------------------

@router.post(
    "/query/nearby",
    response_model=SpatialQueryResponse,
    summary="Find parcels within a radius of a lat/lon point",
)
async def query_nearby(
    body: NearbyQueryRequest,
    db: AsyncSession = Depends(get_db),
) -> SpatialQueryResponse:
    """
    Return parcels within `radius_metres` of the given WGS84 coordinate,
    ordered by ascending distance.

    Uses PostGIS geography type so distances are computed on the spheroid
    (accurate for any position on Earth, not just near the equator).
    """
    result = await db.execute(
        text(
            """
            SELECT
                g.parcel_id,
                p.bdpr,
                p.ulpin,
                p.state_code,
                p.district_code,
                p.is_urban,
                g.area_sq_m,
                g.accuracy_class,
                ST_Distance(
                    g.geometry::geography,
                    ST_SetSRID(ST_Point(:lon, :lat), 4326)::geography
                ) AS distance_metres
            FROM geo.parcel_geometries g
            JOIN identity.parcels p
              ON p.id = g.parcel_id
            WHERE g.is_active = true
              AND p.is_active = true
              AND ST_DWithin(
                    g.geometry::geography,
                    ST_SetSRID(ST_Point(:lon, :lat), 4326)::geography,
                    :radius_metres
                  )
            ORDER BY distance_metres ASC
            """
        ),
        {"lat": body.lat, "lon": body.lon, "radius_metres": body.radius_metres},
    )
    rows = result.mappings().all()

    items = [
        ParcelSpatialResult(
            parcel_id=r["parcel_id"],
            bdpr=r["bdpr"],
            ulpin=r["ulpin"],
            state_code=r["state_code"],
            district_code=r["district_code"],
            is_urban=r["is_urban"],
            area_sq_m=float(r["area_sq_m"]) if r["area_sq_m"] is not None else None,
            accuracy_class=r["accuracy_class"],
            distance_metres=float(r["distance_metres"]),
        )
        for r in rows
    ]
    return SpatialQueryResponse(items=items, count=len(items))


# ---------------------------------------------------------------------------
# GET /api/v1/geo/conflicts
# ---------------------------------------------------------------------------

@router.get(
    "/conflicts",
    response_model=ConflictListResponse,
    summary="List open topology conflicts (paginated)",
)
async def list_conflicts(
    conflict_type: Optional[str] = Query(
        None,
        description="Filter by type: OVERLAP, GAP, SLIVER, SELF_INTERSECTION",
    ),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(50, ge=1, le=200, description="Results per page"),
    db: AsyncSession = Depends(get_db),
) -> ConflictListResponse:
    """
    Return all open (unresolved) topology conflicts, paginated.

    Optionally filter by `conflict_type`.  Ordered by detection date descending
    so the newest conflicts appear first.
    """
    where_clause = "WHERE tc.resolution_status = 'OPEN'"
    params: Dict[str, Any] = {}

    if conflict_type:
        allowed = {"OVERLAP", "GAP", "SLIVER", "SELF_INTERSECTION"}
        if conflict_type.upper() not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid conflict_type. Allowed: {sorted(allowed)}",
            )
        where_clause += " AND tc.conflict_type = :conflict_type"
        params["conflict_type"] = conflict_type.upper()

    # Count
    count_result = await db.execute(
        text(f"SELECT COUNT(*) FROM geo.topology_conflicts tc {where_clause}"),
        params,
    )
    total = count_result.scalar_one()

    # Fetch page
    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset
    data_result = await db.execute(
        text(
            f"""
            SELECT
                tc.id,
                tc.conflict_type,
                tc.parcel_id_1,
                tc.parcel_id_2,
                tc.overlap_area_sq_m,
                tc.detected_at,
                tc.resolution_status
            FROM geo.topology_conflicts tc
            {where_clause}
            ORDER BY tc.detected_at DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    )
    rows = data_result.mappings().all()

    items = [
        TopologyConflictResponse(
            id=r["id"],
            conflict_type=r["conflict_type"],
            parcel_id_1=r["parcel_id_1"],
            parcel_id_2=r["parcel_id_2"],
            overlap_area_sq_m=float(r["overlap_area_sq_m"]) if r["overlap_area_sq_m"] else None,
            detected_at=r["detected_at"],
            resolution_status=r["resolution_status"],
        )
        for r in rows
    ]
    return ConflictListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# POST /api/v1/geo/conflicts/detect/{parcel_id}
# ---------------------------------------------------------------------------

@router.post(
    "/conflicts/detect/{parcel_id}",
    response_model=ConflictDetectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Run on-demand topology conflict detection for a parcel",
)
async def detect_conflicts(
    parcel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ConflictDetectionResponse:
    """
    Trigger an immediate topology check for the given parcel.

    Detects **overlapping** parcels using ST_Overlaps on the active geometry.
    The overlap area is computed using ST_Intersection on the geography type
    (spheroidal area, accurate in square metres).

    Results are returned in the response only — they are NOT automatically
    persisted to `geo.topology_conflicts`.  Call this endpoint to preview;
    use the conflict management API to persist after human review.
    """
    # Verify parcel exists and has an active geometry
    check_result = await db.execute(
        text(
            """
            SELECT g.id
            FROM geo.parcel_geometries g
            WHERE g.parcel_id = :parcel_id
              AND g.is_active = true
            LIMIT 1
            """
        ),
        {"parcel_id": str(parcel_id)},
    )
    if check_result.fetchone() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active geometry found for parcel {parcel_id}",
        )

    # Detect overlaps
    overlap_result = await db.execute(
        text(
            """
            SELECT
                p2.bdpr                    AS overlapping_bdpr,
                g2.parcel_id               AS overlapping_parcel_id,
                ST_Area(
                    ST_Intersection(
                        g1.geometry::geography,
                        g2.geometry::geography
                    )
                )                          AS overlap_area_sq_m
            FROM geo.parcel_geometries g1
            JOIN geo.parcel_geometries g2
              ON g1.parcel_id != g2.parcel_id
            JOIN identity.parcels p2
              ON g2.parcel_id = p2.id
            WHERE g1.parcel_id = :parcel_id
              AND g1.is_active  = true
              AND g2.is_active  = true
              AND p2.is_active  = true
              AND ST_Overlaps(g1.geometry, g2.geometry)
            ORDER BY overlap_area_sq_m DESC
            """
        ),
        {"parcel_id": str(parcel_id)},
    )
    overlap_rows = overlap_result.mappings().all()

    overlaps = [
        DetectedOverlap(
            overlapping_bdpr=r["overlapping_bdpr"],
            overlapping_parcel_id=r["overlapping_parcel_id"],
            overlap_area_sq_m=float(r["overlap_area_sq_m"]),
        )
        for r in overlap_rows
    ]

    logger.info(
        "topology.conflict_detection.complete",
        parcel_id=str(parcel_id),
        overlaps_found=len(overlaps),
    )

    return ConflictDetectionResponse(
        parcel_id=parcel_id,
        overlaps_found=len(overlaps),
        overlaps=overlaps,
        checked_at=datetime.now(timezone.utc),
    )
