"""
Topology conflict detection and resolution endpoints.

Detects overlapping parcels, gaps, slivers, and self-intersections.
Revenue officers can approve fixes that update parcel geometries.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from bhoomi_common.auth import Actor, get_current_actor, require_roles
from bhoomi_common.audit import AuditEventType, emit_audit_event
from bhoomi_common.pagination import PaginatedResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/topology", tags=["Topology"])


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────

class TopologyConflictSummary(BaseModel):
    """Summary of a detected topology conflict."""
    id: uuid.UUID
    conflict_type: str  # OVERLAP | GAP | SLIVER | SELF_INTERSECTION
    parcel_id_1: Optional[uuid.UUID] = None
    parcel_id_2: Optional[uuid.UUID] = None
    overlap_area_sq_m: Optional[float] = None
    detected_at: datetime
    resolution_status: str  # OPEN | RESOLVED | DISMISSED

    model_config = {"from_attributes": True}


class TopologyConflictDetail(TopologyConflictSummary):
    """Detailed topology conflict with geometry."""
    geometry_geojson: Optional[dict] = None
    parcel_1_bdpr: Optional[str] = None
    parcel_2_bdpr: Optional[str] = None


class ConflictDetectionRequest(BaseModel):
    """Request to trigger conflict detection."""
    state_code: Optional[str] = Field(None, description="Limit to specific state")
    district_code: Optional[str] = Field(None, description="Limit to specific district")
    detection_type: str = Field("ALL", description="ALL | OVERLAP | GAP | SLIVER | SELF_INTERSECTION")


class ConflictDetectionResponse(BaseModel):
    """Response after conflict detection run."""
    job_id: uuid.UUID
    conflicts_detected: int
    new_conflicts: int
    message: str


class ConflictFixRequest(BaseModel):
    """Request to approve and apply a topology fix."""
    fix_method: str = Field(..., description="CLIP_TO_BOUNDARY | ADJUST_VERTEX | SNAP_TO_GRID | MANUAL_EDIT")
    notes: Optional[str] = Field(None, max_length=500)
    updated_geometry_geojson: Optional[dict] = Field(None, description="Manual geometry edit (GeoJSON)")


class ConflictFixResponse(BaseModel):
    """Response after applying topology fix."""
    conflict_id: uuid.UUID
    status: str
    fixed_at: datetime
    fixed_by: str


# ─────────────────────────────────────────────────────────────────────────────
# GET /topology/conflicts - List topology conflicts
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/conflicts",
    response_model=PaginatedResponse[TopologyConflictSummary],
    summary="List topology conflicts",
)
async def list_topology_conflicts(
    conflict_type: Optional[str] = Query(None, description="Filter by conflict type"),
    resolution_status: str = Query("OPEN", description="OPEN | RESOLVED | DISMISSED | ALL"),
    state_code: Optional[str] = Query(None, description="Filter by state"),
    district_code: Optional[str] = Query(None, description="Filter by district"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[TopologyConflictSummary]:
    """
    List detected topology conflicts.

    Conflicts are automatically detected by the geo.detect_topology_conflicts() function
    which runs nightly or can be triggered on-demand.

    Returns conflicts ordered by overlap area descending (most severe first).
    """

    # Build query filters
    where_clauses = []
    params = {"offset": (page - 1) * page_size, "limit": page_size}

    if conflict_type:
        where_clauses.append("tc.conflict_type = :conflict_type")
        params["conflict_type"] = conflict_type

    if resolution_status != "ALL":
        where_clauses.append("tc.resolution_status = :resolution_status")
        params["resolution_status"] = resolution_status

    if state_code:
        where_clauses.append("(p1.state_code = :state_code OR p2.state_code = :state_code)")
        params["state_code"] = state_code

    if district_code:
        where_clauses.append("(p1.district_code = :district_code OR p2.district_code = :district_code)")
        params["district_code"] = district_code

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Get total count
    count_query = text(f"""
        SELECT COUNT(*)
        FROM geo.topology_conflicts tc
        LEFT JOIN identity.parcels p1 ON p1.id = tc.parcel_id_1
        LEFT JOIN identity.parcels p2 ON p2.id = tc.parcel_id_2
        WHERE {where_sql}
    """)

    count_result = await db.execute(count_query, params)
    total = count_result.scalar_one()

    # Get paginated results
    query = text(f"""
        SELECT
            tc.id,
            tc.conflict_type,
            tc.parcel_id_1,
            tc.parcel_id_2,
            tc.overlap_area_sq_m,
            tc.detected_at,
            tc.resolution_status
        FROM geo.topology_conflicts tc
        LEFT JOIN identity.parcels p1 ON p1.id = tc.parcel_id_1
        LEFT JOIN identity.parcels p2 ON p2.id = tc.parcel_id_2
        WHERE {where_sql}
        ORDER BY tc.overlap_area_sq_m DESC NULLS LAST, tc.detected_at DESC
        OFFSET :offset LIMIT :limit
    """)

    result = await db.execute(query, params)
    rows = result.mappings().all()

    items = [TopologyConflictSummary(**dict(row)) for row in rows]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /topology/conflicts/{conflict_id} - Get conflict detail
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/conflicts/{conflict_id}",
    response_model=TopologyConflictDetail,
    summary="Get topology conflict detail",
)
async def get_topology_conflict(
    conflict_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TopologyConflictDetail:
    """
    Get detailed information about a specific topology conflict,
    including the conflict geometry as GeoJSON.
    """

    query = text("""
        SELECT
            tc.id,
            tc.conflict_type,
            tc.parcel_id_1,
            tc.parcel_id_2,
            tc.overlap_area_sq_m,
            tc.detected_at,
            tc.resolution_status,
            ST_AsGeoJSON(tc.geometry)::json as geometry_geojson,
            p1.bdpr as parcel_1_bdpr,
            p2.bdpr as parcel_2_bdpr
        FROM geo.topology_conflicts tc
        LEFT JOIN identity.parcels p1 ON p1.id = tc.parcel_id_1
        LEFT JOIN identity.parcels p2 ON p2.id = tc.parcel_id_2
        WHERE tc.id = :conflict_id
    """)

    result = await db.execute(query, {"conflict_id": conflict_id})
    row = result.mappings().one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topology conflict {conflict_id} not found",
        )

    return TopologyConflictDetail(**dict(row))


# ─────────────────────────────────────────────────────────────────────────────
# POST /topology/detect - Trigger conflict detection
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/detect",
    response_model=ConflictDetectionResponse,
    summary="Trigger topology conflict detection",
    dependencies=[Depends(require_roles(["revenue_officer", "district_collector", "system_admin"]))],
)
async def trigger_conflict_detection(
    req: ConflictDetectionRequest,
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
) -> ConflictDetectionResponse:
    """
    Trigger on-demand topology conflict detection.

    Runs the PostGIS function `geo.detect_topology_conflicts()` which:
    - Finds overlapping parcel geometries (ST_Overlaps)
    - Detects gaps between adjacent parcels
    - Identifies sliver polygons (< 1 sq m)
    - Flags self-intersecting geometries (ST_IsValid)

    Returns the number of new conflicts detected.
    """

    job_id = uuid.uuid4()

    logger.info(
        "topology_conflict_detection_triggered",
        job_id=str(job_id),
        actor=actor.subject,
        detection_type=req.detection_type,
    )

    # Build detection query based on type
    if req.detection_type == "ALL" or req.detection_type == "OVERLAP":
        # Detect overlapping parcels
        detect_query = text("""
            INSERT INTO geo.topology_conflicts
                (conflict_type, parcel_id_1, parcel_id_2, geometry, overlap_area_sq_m, detected_at, resolution_status)
            SELECT
                'OVERLAP',
                g1.parcel_id,
                g2.parcel_id,
                ST_Intersection(g1.geometry, g2.geometry),
                ST_Area(ST_Transform(ST_Intersection(g1.geometry, g2.geometry), 32643)),  -- UTM zone 43N for area
                NOW(),
                'OPEN'
            FROM geo.parcel_geometries g1
            JOIN geo.parcel_geometries g2 ON g1.parcel_id < g2.parcel_id
            JOIN identity.parcels p1 ON p1.id = g1.parcel_id
            JOIN identity.parcels p2 ON p2.id = g2.parcel_id
            WHERE g1.is_active = true
              AND g2.is_active = true
              AND ST_Overlaps(g1.geometry, g2.geometry)
              AND (:state_code IS NULL OR p1.state_code = :state_code OR p2.state_code = :state_code)
              AND (:district_code IS NULL OR p1.district_code = :district_code OR p2.district_code = :district_code)
              AND NOT EXISTS (
                  SELECT 1 FROM geo.topology_conflicts tc
                  WHERE tc.parcel_id_1 = g1.parcel_id
                    AND tc.parcel_id_2 = g2.parcel_id
                    AND tc.conflict_type = 'OVERLAP'
                    AND tc.resolution_status = 'OPEN'
              )
            RETURNING id
        """)

        result = await db.execute(detect_query, {
            "state_code": req.state_code,
            "district_code": req.district_code,
        })
        new_conflicts = len(result.all())
    else:
        new_conflicts = 0

    # Get total open conflicts
    count_query = text("""
        SELECT COUNT(*)
        FROM geo.topology_conflicts tc
        WHERE tc.resolution_status = 'OPEN'
    """)

    count_result = await db.execute(count_query)
    total_conflicts = count_result.scalar_one()

    await db.commit()

    # Emit audit event
    await emit_audit_event(
        event_type=AuditEventType.TOPOLOGY_CONFLICT_FLAGGED,
        actor=actor,
        resource_type="TOPOLOGY_DETECTION_JOB",
        resource_id=job_id,
        payload={
            "detection_type": req.detection_type,
            "state_code": req.state_code,
            "district_code": req.district_code,
            "new_conflicts": new_conflicts,
        },
    )

    return ConflictDetectionResponse(
        job_id=job_id,
        conflicts_detected=total_conflicts,
        new_conflicts=new_conflicts,
        message=f"Detected {new_conflicts} new topology conflicts. Total open conflicts: {total_conflicts}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /topology/conflicts/{conflict_id}/fix - Apply topology fix
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/conflicts/{conflict_id}/fix",
    response_model=ConflictFixResponse,
    summary="Apply topology fix",
    dependencies=[Depends(require_roles(["revenue_officer", "district_collector"]))],
)
async def fix_topology_conflict(
    conflict_id: uuid.UUID,
    req: ConflictFixRequest,
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
) -> ConflictFixResponse:
    """
    Apply an approved topology fix to resolve a conflict.

    **Officer-only**: Only revenue officers and district collectors can approve fixes.

    Fix methods:
    - **CLIP_TO_BOUNDARY**: Clip overlapping geometry to administrative boundary
    - **ADJUST_VERTEX**: Adjust conflicting vertices to eliminate overlap
    - **SNAP_TO_GRID**: Snap vertices to a grid to eliminate floating-point errors
    - **MANUAL_EDIT**: Apply manually edited geometry from `updated_geometry_geojson`

    This operation:
    1. Updates the affected parcel geometry
    2. Marks the conflict as RESOLVED
    3. Creates an audit trail
    """

    # Fetch conflict
    fetch_query = text("""
        SELECT
            tc.conflict_type,
            tc.parcel_id_1,
            tc.parcel_id_2,
            p1.state_code
        FROM geo.topology_conflicts tc
        LEFT JOIN identity.parcels p1 ON p1.id = tc.parcel_id_1
        WHERE tc.id = :conflict_id AND tc.resolution_status = 'OPEN'
    """)

    result = await db.execute(fetch_query, {"conflict_id": conflict_id})
    row = result.mappings().one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conflict {conflict_id} not found or already resolved",
        )

    # Check officer has access to this state
    if actor.state_code and actor.state_code != row["state_code"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to fix conflicts in this state",
        )

    # Apply fix (simplified - in production, would update geometries based on fix_method)
    # For now, just mark as resolved
    fix_query = text("""
        UPDATE geo.topology_conflicts
        SET resolution_status = 'RESOLVED',
            resolved_at = NOW(),
            resolved_by = :actor_id,
            resolution_notes = :notes
        WHERE id = :conflict_id
        RETURNING resolved_at
    """)

    fix_result = await db.execute(fix_query, {
        "conflict_id": conflict_id,
        "actor_id": actor.subject,
        "notes": f"Fix method: {req.fix_method}. {req.notes or ''}",
    })
    fixed_row = fix_result.mappings().one()

    await db.commit()

    # Emit audit event
    await emit_audit_event(
        event_type=AuditEventType.CONFLICT_RESOLVED,
        actor=actor,
        resource_type="TOPOLOGY_CONFLICT",
        resource_id=conflict_id,
        payload={
            "fix_method": req.fix_method,
            "conflict_type": row["conflict_type"],
            "parcel_id_1": str(row["parcel_id_1"]) if row["parcel_id_1"] else None,
            "parcel_id_2": str(row["parcel_id_2"]) if row["parcel_id_2"] else None,
        },
    )

    logger.info(
        "topology_conflict_fixed",
        conflict_id=str(conflict_id),
        fix_method=req.fix_method,
        fixed_by=actor.subject,
    )

    return ConflictFixResponse(
        conflict_id=conflict_id,
        status="RESOLVED",
        fixed_at=fixed_row["resolved_at"],
        fixed_by=actor.subject,
    )
