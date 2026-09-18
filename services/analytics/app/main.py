import time
import uuid
from contextlib import asynccontextmanager

import httpx
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db import engine
from app.routers import health, analytics, nl_query

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient()
    logger.info("startup", service=settings.service_name)
    yield
    await engine.dispose()
    await app.state.http_client.aclose()
    logger.info("shutdown", service=settings.service_name)


app = FastAPI(
    title="Analytics Service",
    version="1.0.0",
    description="Dashboard aggregations, KPIs, and service delivery metrics for Bhoomi Dhrishti.",
    lifespan=lifespan,
)

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
    request.state.request_id = request_id
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info(
        "request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round(duration * 1000, 2),
        request_id=request_id,
    )
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": {"code": "NOT_FOUND", "message": "Resource not found", "detail": {}}},
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error", "detail": {}}},
    )


app.include_router(health.router, tags=["health"])
app.include_router(analytics.router, tags=["analytics"])
app.include_router(nl_query.router)
