"""
Geospatial Service – FastAPI application entry point.

Serves:
- GeoJSON geometry for parcels
- Mapbox Vector Tiles (MVT) for MapLibre GL JS
- OGC WFS 2.0 / WMS 1.3.0 GetCapabilities stubs
- Spatial queries (within-polygon, nearby, conflict detection)
"""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db import close_db, init_db
from bhoomi_common.errors import register_exception_handlers

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Structured logging setup
# ---------------------------------------------------------------------------

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # ── Startup ──────────────────────────────────────────────────────────────
    logger.info("service.startup", service=settings.SERVICE_NAME)
    await init_db(pool_size=10, max_overflow=20, pool_timeout=30)
    app.state.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(5.0),
        headers={"User-Agent": f"bhoomi/{settings.SERVICE_NAME}"},
    )
    logger.info("service.startup.complete", service=settings.SERVICE_NAME)
    yield
    # ── Shutdown ─────────────────────────────────────────────────────────────
    await close_db()
    await app.state.http_client.aclose()
    logger.info("service.shutdown", service=settings.SERVICE_NAME)


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Bhoomi Dhrishti – Geospatial Service",
    description=(
        "PostGIS-powered geospatial API for the Bhoomi Dhrishti land governance "
        "platform.  Serves vector tiles, GeoJSON geometries, OGC capabilities, "
        "and spatial query results. (SIH 2026, PS-26014)"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.monotonic()

    log = logger.bind(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )
    log.info("request.start")

    response = await call_next(request)

    duration_ms = round((time.monotonic() - start_time) * 1000, 2)
    log.info(
        "request.complete",
        status_code=response.status_code,
        duration_ms=duration_ms,
    )

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Service"] = settings.SERVICE_NAME
    return response


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

register_exception_handlers(app)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

from app.routers import health, geometry, tiles, ogc, spatial_query, topology  # noqa: E402

app.include_router(health.router)
app.include_router(tiles.router, prefix="/api/v1")
app.include_router(geometry.router, prefix="/api/v1")
app.include_router(spatial_query.router, prefix="/api/v1")
app.include_router(topology.router, prefix="/api/v1")
app.include_router(ogc.router)  # /ogc/wfs and /ogc/wms (no /api/v1 prefix — OGC convention)


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
async def root():
    return JSONResponse(
        content={
            "service": settings.SERVICE_NAME,
            "version": "1.0.0",
            "docs": "/docs",
            "tile_endpoint": "/api/v1/geo/tiles/{layer}/{z}/{x}/{y}.mvt",
            "wfs": "/ogc/wfs?service=WFS&request=GetCapabilities",
            "wms": "/ogc/wms?service=WMS&request=GetCapabilities",
        }
    )
