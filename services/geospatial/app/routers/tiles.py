"""
Vector Tile (MVT) endpoint — the most performance-critical route in the system.

Returns Mapbox Vector Tiles (protobuf binary) at the standard {z}/{x}/{y}
addressing scheme.  MapLibre GL JS consumes these directly.

Design decisions:
- All tile SQL runs inside PostgreSQL using ST_AsMVT + ST_AsMVTGeom.
  The DB does the geometry clipping, simplification, and encoding.
- We return raw bytes; FastAPI/uvicorn streams them unchanged.
- Empty tiles (no features) return HTTP 204 so MapLibre skips rendering.
- Cache-Control headers let Nginx/Varnish cache tiles at the edge.
- z/x/y inputs are validated to prevent SQL injection via bind params.
- LEFT JOINs against revenue.records_of_rights and ml.conflict_scores
  are safe even when those services haven't inserted data yet.

Supported layers:
  parcels            – identity.parcels + geo.parcel_geometries
  admin_districts    – geo.administrative_boundaries
  restriction_zones  – geo.restriction_zones
  conflicts          – geo.topology_conflicts (open only)
"""

from __future__ import annotations

from typing import Final, Set

import structlog
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import text

from app.config import settings
from app.db import get_engine

logger = structlog.get_logger()

router = APIRouter(prefix="/geo/tiles", tags=["Vector Tiles"])

# Supported layer names
VALID_LAYERS: Final[Set[str]] = {
    "parcels",
    "admin_districts",
    "restriction_zones",
    "conflicts",
}

_CONTENT_TYPE_MVT: Final[str] = "application/x-protobuf"


# ---------------------------------------------------------------------------
# SQL builders
# ---------------------------------------------------------------------------

_PARCELS_TILE_SQL = text(
    """
    WITH bounds AS (
      SELECT
        ST_Transform(ST_TileEnvelope(:z, :x, :y), 4326) AS env4326,
        ST_TileEnvelope(:z, :x, :y)                     AS env3857
    )
    SELECT ST_AsMVT(q, 'parcels', 4096, 'geom') AS mvt
    FROM (
      SELECT
        p.bdpr,
        p.ulpin,
        p.is_urban,
        g.area_sq_m,
        g.accuracy_class,
        COALESCE(r.land_use, 'UNKNOWN')  AS land_use,
        EXISTS(
          SELECT 1
          FROM geo.topology_conflicts tc
          WHERE (tc.parcel_id_1 = p.id OR tc.parcel_id_2 = p.id)
            AND tc.resolution_status = 'OPEN'
        )                                AS has_conflict,
        COALESCE(ms.risk_band, 'UNKNOWN') AS risk_band,
        ST_AsMVTGeom(
          ST_Transform(g.geometry, 3857),
          bounds.env3857,
          4096, 256, true
        ) AS geom
      FROM geo.parcel_geometries g
      JOIN identity.parcels p
        ON p.id = g.parcel_id
      LEFT JOIN revenue.records_of_rights r
        ON r.parcel_id = p.id
      LEFT JOIN ml.conflict_scores ms
        ON ms.parcel_id = p.id AND ms.score_type = 'ANOMALY'
      CROSS JOIN bounds
      WHERE ST_Intersects(g.geometry, bounds.env4326)
        AND g.is_active  = true
        AND p.is_active  = true
    ) q
    """
)

_ADMIN_TILE_SQL = text(
    """
    WITH bounds AS (
      SELECT
        ST_Transform(ST_TileEnvelope(:z, :x, :y), 4326) AS env4326,
        ST_TileEnvelope(:z, :x, :y)                     AS env3857
    )
    SELECT ST_AsMVT(q, 'admin_districts', 4096, 'geom') AS mvt
    FROM (
      SELECT
        b.lgd_code,
        b.name_en,
        b.name_local,
        b.level,
        b.hierarchy_type,
        ST_AsMVTGeom(
          ST_Transform(b.geometry, 3857),
          bounds.env3857,
          4096, 256, true
        ) AS geom
      FROM geo.administrative_boundaries b
      CROSS JOIN bounds
      WHERE ST_Intersects(b.geometry, bounds.env4326)
    ) q
    """
)

_RESTRICTION_TILE_SQL = text(
    """
    WITH bounds AS (
      SELECT
        ST_Transform(ST_TileEnvelope(:z, :x, :y), 4326) AS env4326,
        ST_TileEnvelope(:z, :x, :y)                     AS env3857
    )
    SELECT ST_AsMVT(q, 'restriction_zones', 4096, 'geom') AS mvt
    FROM (
      SELECT
        rz.zone_type,
        rz.name,
        rz.legal_basis,
        CAST(rz.buffer_metres AS FLOAT) AS buffer_metres,
        ST_AsMVTGeom(
          ST_Transform(rz.geometry, 3857),
          bounds.env3857,
          4096, 256, true
        ) AS geom
      FROM geo.restriction_zones rz
      CROSS JOIN bounds
      WHERE ST_Intersects(rz.geometry, bounds.env4326)
    ) q
    """
)

_CONFLICTS_TILE_SQL = text(
    """
    WITH bounds AS (
      SELECT
        ST_Transform(ST_TileEnvelope(:z, :x, :y), 4326) AS env4326,
        ST_TileEnvelope(:z, :x, :y)                     AS env3857
    )
    SELECT ST_AsMVT(q, 'conflicts', 4096, 'geom') AS mvt
    FROM (
      SELECT
        tc.conflict_type,
        CAST(tc.overlap_area_sq_m AS FLOAT) AS overlap_area_sq_m,
        tc.resolution_status,
        tc.parcel_id_1::text AS parcel_id_1,
        tc.parcel_id_2::text AS parcel_id_2,
        ST_AsMVTGeom(
          ST_Transform(tc.geometry, 3857),
          bounds.env3857,
          4096, 256, true
        ) AS geom
      FROM geo.topology_conflicts tc
      CROSS JOIN bounds
      WHERE ST_Intersects(tc.geometry, bounds.env4326)
        AND tc.resolution_status = 'OPEN'
    ) q
    """
)

_LAYER_SQL = {
    "parcels": _PARCELS_TILE_SQL,
    "admin_districts": _ADMIN_TILE_SQL,
    "restriction_zones": _RESTRICTION_TILE_SQL,
    "conflicts": _CONFLICTS_TILE_SQL,
}


# ---------------------------------------------------------------------------
# Tile endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/{layer}/{z}/{x}/{y}.mvt",
    summary="Serve a Mapbox Vector Tile (MVT) for the given layer",
    responses={
        200: {
            "content": {"application/x-protobuf": {}},
            "description": "MVT tile bytes",
        },
        204: {"description": "Tile exists but contains no features"},
        400: {"description": "Unknown layer or invalid z/x/y"},
    },
)
async def get_tile(layer: str, z: int, x: int, y: int) -> Response:
    """
    Serve a Mapbox Vector Tile for `layer` at zoom/x/y.

    Tiles are generated on-the-fly by PostGIS ST_AsMVT.  The result is
    streamed as raw protobuf bytes with `Content-Type: application/x-protobuf`.

    **Performance notes**:
    - Tile generation happens entirely inside PostgreSQL — no geometry
      deserialisation in Python.
    - Empty tiles (no features intersecting the tile envelope) return
      HTTP 204 so the client doesn't need to parse an empty protobuf.
    - Set `Cache-Control: max-age=<TILE_CACHE_MAX_AGE>` for edge caching.

    **Layer names**: `parcels`, `admin_districts`, `restriction_zones`, `conflicts`
    """
    # ── Input validation ──────────────────────────────────────────────────────
    if layer not in VALID_LAYERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown layer '{layer}'. Valid layers: {sorted(VALID_LAYERS)}",
        )

    max_tile = 2**z - 1
    if z < 0 or z > settings.TILE_MAX_ZOOM:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Zoom level {z} out of range [0, {settings.TILE_MAX_ZOOM}]",
        )
    if x < 0 or x > max_tile or y < 0 or y > max_tile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tile coordinates ({x}, {y}) out of range for zoom {z}",
        )

    # ── Execute tile SQL ──────────────────────────────────────────────────────
    sql = _LAYER_SQL[layer]
    params = {"z": z, "x": x, "y": y}

    engine = get_engine()
    async with engine.connect() as conn:
        result = await conn.execute(sql, params)
        row = result.fetchone()

    mvt_bytes: bytes | None = row[0] if row else None

    # ── Empty tile: 204 ───────────────────────────────────────────────────────
    if not mvt_bytes:
        logger.debug("tile.empty", layer=layer, z=z, x=x, y=y)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    # ── Return MVT bytes ──────────────────────────────────────────────────────
    logger.debug(
        "tile.served",
        layer=layer,
        z=z,
        x=x,
        y=y,
        bytes=len(mvt_bytes),
    )
    return Response(
        content=mvt_bytes,
        media_type=_CONTENT_TYPE_MVT,
        headers={
            "Cache-Control": f"public, max-age={settings.TILE_CACHE_MAX_AGE}",
            "Access-Control-Allow-Origin": "*",
            "Content-Encoding": "identity",  # MVT is not gzip; be explicit
        },
    )
