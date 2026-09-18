"""
trust-engine service � FastAPI application.

Cross-registry conflict detection, confidence scoring and dispute resolution workflow
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from bhoomi_common.db import init_db, close_db
from bhoomi_common.errors import register_exception_handlers
from app.routers import health, anomalies, graph

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer() if os.environ.get("LOG_FORMAT") == "json"
        else structlog.dev.ConsoleRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)
logger = structlog.get_logger(__name__)

SERVICE_NAME = "trust-engine"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("service.startup", service=SERVICE_NAME)
    await init_db(pool_size=int(os.environ.get("DB_POOL_SIZE", "5")))
    logger.info("service.ready", service=SERVICE_NAME)
    yield
    await close_db()
    logger.info("service.shutdown", service=SERVICE_NAME)


app = FastAPI(
    title="Bhoomi Dhrishti � Trust Engine",
    description="Cross-registry conflict detection, confidence scoring and dispute resolution workflow",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")
register_exception_handlers(app)
app.include_router(health.router, tags=["Health"])
app.include_router(anomalies.router)
app.include_router(graph.router)
