"""Health and readiness endpoints for the trust-engine service."""

import os
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from bhoomi_common.db import check_db_health

router = APIRouter()

SERVICE_NAME = "trust-engine"
START_TIME = datetime.now(tz=timezone.utc)


@router.get("/health", summary="Liveness probe")
async def health():
    return {"status": "ok", "service": SERVICE_NAME, "timestamp": datetime.now(tz=timezone.utc).isoformat()}


@router.get("/ready", summary="Readiness probe")
async def ready():
    db_health = await check_db_health()
    is_ready = db_health["status"] == "healthy"
    body = {
        "status": "ready" if is_ready else "not_ready",
        "service": SERVICE_NAME,
        "uptime_seconds": (datetime.now(tz=timezone.utc) - START_TIME).total_seconds(),
        "checks": {"database": db_health},
    }
    return JSONResponse(content=body, status_code=200 if is_ready else 503)
