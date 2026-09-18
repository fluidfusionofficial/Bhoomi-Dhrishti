from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db import get_db

router = APIRouter()


@router.get("/health")
async def health():
    """Basic liveness probe — always returns 200 if the process is up."""
    return {"status": "ok", "service": "revenue-records"}


@router.get("/health/ready")
async def ready(db: AsyncSession = Depends(get_db)):
    """Readiness probe — checks DB connectivity."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "service": "revenue-records", "db": "ok"}
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Database not reachable",
                    "detail": {"reason": str(exc)},
                }
            },
        )
