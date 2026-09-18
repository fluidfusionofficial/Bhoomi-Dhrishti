"""
Spatial-first entity resolution using PostGIS geometry overlap.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from shapely import wkt
from shapely.geometry import Point, shape, mapping
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .types import LinkCandidate


class SpatialResolver:
    """Resolves entities using spatial geometry overlap (strongest signal)."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def find_match(
        self,
        record: Dict[str, Any],
        iou_threshold: float = 0.7,
    ) -> Optional[LinkCandidate]:
        """
        Find matching parcel using spatial overlap (IoU >= threshold).

        Args:
            record: Source record with 'geometry' (WKT/GeoJSON) or 'latitude'/'longitude'
            iou_threshold: Minimum intersection-over-union for match (default 0.7)

        Returns:
            LinkCandidate if match found, else None
        """
        # Extract geometry
        geom_wkt = None

        if 'geometry' in record:
            geom = record['geometry']
            if isinstance(geom, str):
                # Assume WKT
                geom_wkt = geom
            elif isinstance(geom, dict):
                # Assume GeoJSON
                try:
                    shapely_geom = shape(geom)
                    geom_wkt = shapely_geom.wkt
                except Exception:
                    return None
        elif 'latitude' in record and 'longitude' in record:
            # Point geometry
            point = Point(record['longitude'], record['latitude'])
            geom_wkt = point.wkt
        else:
            return None

        if not geom_wkt:
            return None

        # Query for overlapping parcels with IoU calculation
        query = text("""
            WITH input AS (
                SELECT ST_GeomFromText(:geom_wkt, 4326) AS geom
            ),
            candidates AS (
                SELECT
                    p.parcel_id,
                    pg.geometry,
                    ST_Area(ST_Intersection(pg.geometry, input.geom)) /
                    ST_Area(ST_Union(pg.geometry, input.geom)) AS iou
                FROM geo.parcel_geometries pg
                JOIN identity.parcels p ON p.parcel_id = pg.parcel_id
                CROSS JOIN input
                WHERE ST_Intersects(pg.geometry, input.geom)
            )
            SELECT
                parcel_id,
                ST_AsText(geometry) AS geometry_wkt,
                iou
            FROM candidates
            WHERE iou >= :iou_threshold
            ORDER BY iou DESC
            LIMIT 1
        """)

        result = await self.db.execute(query, {
            "geom_wkt": geom_wkt,
            "iou_threshold": iou_threshold,
        })
        row = result.fetchone()

        if row:
            return LinkCandidate(
                source_record_id=record.get('id') or record.get('survey_number', 'unknown'),
                target_parcel_id=row.parcel_id,
                confidence_score=row.iou,  # IoU as confidence
                match_method="SPATIAL",
                evidence={
                    "iou": round(row.iou, 4),
                    "method": "geometry_overlap",
                    "matched_geometry": row.geometry_wkt[:500],  # Truncate for storage
                },
                status="CONFIRMED" if row.iou >= 0.85 else "POSSIBLE",
            )

        return None
