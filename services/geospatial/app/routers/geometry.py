"""
Parcel geometry endpoints.

All geometry is returned as GeoJSON (RFC 7946).  The actual PostGIS functions
(ST_AsGeoJSON, ST_Intersects, etc.) run inside PostgreSQL via raw SQL so we
avoid pulling binary WKB over the wire and parsing it in Python.
"""

from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.geo import ParcelGeometryResponse, TopologyConflictResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/geo/parcels", tags=["Geometry"])


# ---------------------------------------------------------------------------
# GET /api/v1/geo/parcels/{parcel_id}/geometry
# ---------------------------------------------------------------------------

@router.get(
    "/{parcel_id}/geometry",
    response_model=ParcelGeometryResponse,
    summary="Get active geometry for a parcel as GeoJSON Feature",
    responses={
        404: {"description": "No active geometry found for this parcel"},
    },
)
async def get_parcel_geometry(
    parcel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ParcelGeometryResponse:
    """
    Returns the current (is_active=true) geometry for the given parcel as a
    GeoJSON Feature.

    Properties include:
    - `parcel_id`  – UUID of the parcel
    - `area_sq_m`  – official computed area in square metres
    - `area_native` / `area_unit_native` – area in the survey's native unit
    - `accuracy_class` – A/B/C/D/UNKNOWN per DILRMP classification
    - `source_survey_date` – when the geometry was surveyed
    - `version_number` – version of this geometry record
    """
    row = await db.execute(
        text(
            """
            SELECT
                g.id                         AS geom_id,
                g.parcel_id,
                ST_AsGeoJSON(g.geometry)     AS geojson,
                g.area_sq_m,
                g.area_native,
                g.area_unit_native,
                g.accuracy_class,
                g.source_survey_date,
                g.version_number,
                g.crs_native
            FROM geo.parcel_geometries g
            WHERE g.parcel_id = :parcel_id
              AND g.is_active = true
            ORDER BY g.version_number DESC
            LIMIT 1
            """
        ),
        {"parcel_id": str(parcel_id)},
    )
    rec = row.mappings().first()

    if rec is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active geometry found for parcel {parcel_id}",
        )

    geojson_geom = json.loads(rec["geojson"]) if rec["geojson"] else None

    return ParcelGeometryResponse(
        type="Feature",
        geometry=geojson_geom,
        properties={
            "parcel_id": str(rec["parcel_id"]),
            "area_sq_m": float(rec["area_sq_m"]) if rec["area_sq_m"] is not None else None,
            "area_native": float(rec["area_native"]) if rec["area_native"] is not None else None,
            "area_unit_native": rec["area_unit_native"],
            "accuracy_class": rec["accuracy_class"],
            "source_survey_date": str(rec["source_survey_date"]) if rec["source_survey_date"] else None,
            "version_number": rec["version_number"],
            "crs_native": rec["crs_native"],
        },
    )


# ---------------------------------------------------------------------------
# GET /api/v1/geo/parcels/{parcel_id}/conflicts
# ---------------------------------------------------------------------------

@router.get(
    "/{parcel_id}/conflicts",
    response_model=List[TopologyConflictResponse],
    summary="Get open topology conflicts involving a parcel",
)
async def get_parcel_conflicts(
    parcel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> List[TopologyConflictResponse]:
    """
    Returns all **open** (unresolved) topology conflicts where this parcel
    is either `parcel_id_1` or `parcel_id_2`.

    Conflict types: OVERLAP, GAP, SLIVER, SELF_INTERSECTION.
    """
    result = await db.execute(
        text(
            """
            SELECT
                tc.id,
                tc.conflict_type,
                tc.parcel_id_1,
                tc.parcel_id_2,
                tc.overlap_area_sq_m,
                tc.detected_at,
                tc.resolution_status
            FROM geo.topology_conflicts tc
            WHERE (tc.parcel_id_1 = :parcel_id OR tc.parcel_id_2 = :parcel_id)
              AND tc.resolution_status = 'OPEN'
            ORDER BY tc.detected_at DESC
            """
        ),
        {"parcel_id": str(parcel_id)},
    )
    rows = result.mappings().all()
    return [
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
