"""
Parcel Identity Service – FastAPI application entry point.

This is the spine of the Bhoomi Dhrishti platform.  Every other
microservice resolves parcels via this service's BDPR / ULPIN API.
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
    title="Bhoomi Dhrishti – Parcel Identity Service",
    description=(
        "Canonical parcel identity register for the Bhoomi Dhrishti "
        "land governance platform (SIH 2026, PS-26014). "
        "Every land parcel in India gets a stable BDPR here."
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

    # Attach request_id to bound logger context for this request
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
# Exception handlers (from shared library)
# ---------------------------------------------------------------------------

register_exception_handlers(app)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

from app.routers import health, parcels, resolution, reviews  # noqa: E402 (after app is defined)

app.include_router(health.router)
app.include_router(parcels.router, prefix="/api/v1")
app.include_router(resolution.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")


# ---------------------------------------------------------------------------
# Root redirect
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
async def root():
    return JSONResponse(
        content={
            "service": settings.SERVICE_NAME,
            "version": "1.0.0",
            "docs": "/docs",
        }
    )
