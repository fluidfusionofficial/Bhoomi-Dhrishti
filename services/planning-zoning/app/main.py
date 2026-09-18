"""
planning-zoning service – FastAPI application.

Manages master plan zoning regulations, building permissions, and court dispute linkages.
"""
from __future__ import annotations
import os
from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from bhoomi_common.db import init_db, close_db
from bhoomi_common.errors import register_exception_handlers
from app.routers import health

logger = structlog.get_logger(__name__)
SERVICE_NAME = "planning-zoning"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("service.startup", service=SERVICE_NAME)
    await init_db(pool_size=int(os.environ.get("DB_POOL_SIZE", "5")))
    yield
    await close_db()


app = FastAPI(
    title="Bhoomi Dhrishti – Planning & Zoning Service",
    description="Manages master plan zoning regulations, building permissions, and court dispute linkages",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
register_exception_handlers(app)
app.include_router(health.router, tags=["Health"])
