"""Health and readiness probes."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import settings
from app.db import check_db_health

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Liveness probe")
async def health() -> dict:
    """Return 200 if the service process is alive."""
    return {"status": "ok", "service": settings.SERVICE_NAME}


@router.get("/health/ready", summary="Readiness probe")
async def ready() -> JSONResponse:
    """
    Return 200 only when the DB connection pool is healthy.
    Kubernetes / Docker will stop sending traffic if this returns non-200.
    """
    db_status = await check_db_health()
    if db_status["status"] == "healthy":
        return JSONResponse(
            status_code=200,
            content={
                "status": "ready",
                "service": settings.SERVICE_NAME,
                "db": db_status,
            },
        )
    return JSONResponse(
        status_code=503,
        content={
            "status": "not_ready",
            "service": settings.SERVICE_NAME,
            "db": db_status,
        },
    )
