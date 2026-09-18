from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db import get_db

router = APIRouter()


@router.get("/health")
async def health():
    """Liveness probe — always returns 200 if the process is alive."""
    return {"status": "ok", "service": "registration"}


@router.get("/ready")
async def ready(db: AsyncSession = Depends(get_db)):
    """Readiness probe — verifies database connectivity."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "service": "registration", "db": "connected"}
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "service": "registration",
                "db": "unreachable",
                "detail": str(exc),
            },
        )
