"""
Satellite change detection API endpoints.

Provides access to Sentinel-2 based land-use change detection results.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from bhoomi_common.auth import Actor, get_current_actor
from bhoomi_common.db import get_db
from app.modules.change_detection import (
    ChangeDetectionResult,
    ChangePolygon,
    run_change_detection_pipeline,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/satellite", tags=["Satellite"])

# ─────────────────────────────────────────────────────────────────────────────
# Response Models
# ─────────────────────────────────────────────────────────────────────────────


class ChangeLayer(BaseModel):
    """GeoJSON layer of detected changes."""
    type: str = "FeatureCollection"
    features: List[dict]
    metadata: dict


class AffectedParcel(BaseModel):
    """Parcel affected by land-use change."""
    parcel_id: UUID
    bdpr: str
    change_type: str
    overlap_area_sq_m: float


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/change-detection/{village_code}", response_model=ChangeDetectionResult)
async def get_change_detection(
    village_code: str,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    """
    Get land-use change detection results for a village.

    Analyzes Sentinel-2 imagery (10m resolution) to detect:
    - Agricultural to non-agricultural conversion
    - Encroachment on water bodies
    - Encroachment on forest land
    - Large layout development

    **Important**: 10m resolution is suitable for field-level analysis,
    NOT individual building detection. Use Cartosat-3 or UAV imagery for that.
    """
    logger.info(
        "get_change_detection",
        village_code=village_code,
        actor=actor.subject,
    )

    # Verify village access
    from sqlalchemy import text
    village_query = text("""
        SELECT lgd_code, name_en, state_code, parent_lgd_code AS district_code
        FROM reference.lgd_hierarchy
        WHERE lgd_code = :village_code
            AND entity_type = 'VILLAGE'
            AND is_active = true
    """)

    result = await db.execute(village_query, {"village_code": village_code})
    village_row = result.fetchone()

    if not village_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Village {village_code} not found",
        )

    # Check actor access (officers restricted to their district)
    if "revenue_officer" in actor.roles and actor.district_code:
        if village_row.district_code != actor.district_code:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to village outside your district",
            )

    # Run change detection
    try:
        result = await run_change_detection_pipeline(
            db,
            village_code=village_code,
            data_dir=Path("/data/sentinel2"),  # Configurable path
        )

        logger.info(
            "get_change_detection.complete",
            village_code=village_code,
            change_area=result.change_area_sq_m,
            affected_parcels=len(result.affected_parcels),
        )

        return result

    except Exception as e:
        logger.error("get_change_detection: error", village_code=village_code, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Change detection failed: {str(e)}",
        )


@router.get("/change-layers/{village_code}", response_model=ChangeLayer)
async def get_change_layers(
    village_code: str,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    """
    Get change detection results as GeoJSON layer for mapping.

    Returns polygons of detected changes with properties for visualization.
    """
    logger.info("get_change_layers", village_code=village_code, actor=actor.subject)

    # Run change detection (in production, this would be cached)
    change_result = await run_change_detection_pipeline(
        db,
        village_code=village_code,
    )

    # Query stored change polygons from database
    from sqlalchemy import text
    query = text("""
        SELECT
            id,
            change_type,
            confidence_score,
            change_area_sq_m,
            ST_AsGeoJSON(bounding_geometry) AS geometry_geojson,
            detected_from_date,
            detected_to_date
        FROM ml.land_use_changes
        WHERE parcel_id IN (
            SELECT id FROM identity.parcels WHERE village_code = :village_code
        )
        ORDER BY detected_to_date DESC
        LIMIT 500
    """)

    result = await db.execute(query, {"village_code": village_code})
    rows = result.fetchall()

    # Build GeoJSON features
    features = []
    for row in rows:
        import json
        geometry = json.loads(row.geometry_geojson) if row.geometry_geojson else None

        if geometry:
            features.append({
                "type": "Feature",
                "id": str(row.id),
                "geometry": geometry,
                "properties": {
                    "change_type": row.change_type,
                    "confidence_score": float(row.confidence_score),
                    "change_area_sq_m": float(row.change_area_sq_m),
                    "detected_from_date": row.detected_from_date.isoformat() if row.detected_from_date else None,
                    "detected_to_date": row.detected_to_date.isoformat() if row.detected_to_date else None,
                },
            })

    layer = ChangeLayer(
        features=features,
        metadata={
            "village_code": village_code,
            "feature_count": len(features),
            "resolution_note": "10m resolution. Detects field-level land-use change, not individual buildings.",
        },
    )

    logger.info("get_change_layers.complete", village_code=village_code, features=len(features))
    return layer


@router.get("/affected-parcels/{village_code}", response_model=List[AffectedParcel])
async def get_affected_parcels(
    village_code: str,
    change_type: Optional[str] = Query(None, description="Filter by change type"),
    min_area_sq_m: float = Query(100.0, ge=0, description="Minimum change area"),
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    """
    Get list of parcels affected by detected land-use changes.

    Useful for generating notices or investigation lists.
    """
    logger.info(
        "get_affected_parcels",
        village_code=village_code,
        change_type=change_type,
        actor=actor.subject,
    )

    from sqlalchemy import text

    filters = ["p.village_code = :village_code", "luc.change_area_sq_m >= :min_area_sq_m"]
    params = {"village_code": village_code, "min_area_sq_m": min_area_sq_m}

    if change_type:
        filters.append("luc.change_type = :change_type")
        params["change_type"] = change_type

    where_clause = " AND ".join(filters)

    query = text(f"""
        SELECT
            p.id AS parcel_id,
            p.bdpr,
            luc.change_type,
            luc.change_area_sq_m
        FROM identity.parcels p
        INNER JOIN ml.land_use_changes luc ON p.id = luc.parcel_id
        WHERE {where_clause}
        ORDER BY luc.change_area_sq_m DESC
        LIMIT 200
    """)

    result = await db.execute(query, params)
    rows = result.fetchall()

    affected = []
    for row in rows:
        affected.append(AffectedParcel(
            parcel_id=UUID(str(row.parcel_id)),
            bdpr=row.bdpr,
            change_type=row.change_type,
            overlap_area_sq_m=float(row.change_area_sq_m),
        ))

    logger.info("get_affected_parcels.complete", count=len(affected))
    return affected


@router.get("/resolution-note")
async def get_resolution_note():
    """
    Get information about satellite imagery resolution and limitations.

    Explains what can and cannot be detected at 10m resolution.
    """
    return {
        "sensor": "Sentinel-2",
        "resolution_m": 10,
        "suitable_for": [
            "Field-level land-use change (agriculture to built-up)",
            "Large layout developments (>1000 sq_m)",
            "Encroachment on water bodies and forest land",
            "Major infrastructure projects",
            "Illegal mining and quarrying detection",
        ],
        "not_suitable_for": [
            "Individual building detection",
            "Small structures (<100 sq_m)",
            "Building height estimation",
            "Intra-field crop type discrimination",
        ],
        "recommendation": "For individual building detection, use Cartosat-3 (0.25m) or UAV imagery (5-10cm).",
        "revisit_frequency_days": 5,
        "data_source": "Copernicus Sentinel-2 (ESA)",
    }
