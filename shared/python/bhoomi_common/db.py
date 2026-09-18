"""
bhoomi_common.db – Async SQLAlchemy engine and session factory.

Usage in a FastAPI service:

    from bhoomi_common.db import get_db, init_db

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await init_db()
        yield

    @router.get("/parcels/{id}")
    async def get_parcel(id: UUID, db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(Parcel).where(Parcel.id == id))
        return result.scalar_one_or_none()
"""

from __future__ import annotations

import os
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)

# Module-level singletons (initialised by init_db())
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_database_url() -> str:
    """Read the database URL from environment, with sensible defaults."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        # Construct from parts
        user     = os.environ.get("POSTGRES_USER", "bhoomi")
        password = os.environ.get("POSTGRES_PASSWORD", "")
        host     = os.environ.get("POSTGRES_HOST", "postgres")
        port     = os.environ.get("POSTGRES_PORT", "5432")
        db       = os.environ.get("POSTGRES_DB", "bhoomi")
        url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"
    # Ensure asyncpg driver
    if "postgresql://" in url and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://")
    return url


async def init_db(
    pool_size: int = 10,
    max_overflow: int = 20,
    pool_timeout: int = 30,
    pool_recycle: int = 1800,
    echo: bool = False,
) -> None:
    """
    Initialise the async engine and session factory.
    Call once during application startup (in the lifespan handler).
    """
    global _engine, _session_factory

    database_url = _get_database_url()
    logger.info("Initialising database engine: %s", database_url.split("@")[-1])  # Log host only

    _engine = create_async_engine(
        database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
        pool_pre_ping=True,   # Detect stale connections
        echo=echo,
    )

    _session_factory = async_sessionmaker(
        bind=_engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    logger.info("Database engine initialised successfully.")


async def close_db() -> None:
    """Dispose the engine pool. Call during application shutdown."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        logger.info("Database engine disposed.")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: yields an async database session.
    The session is automatically committed on success or rolled back on exception.

    Usage:
        @router.get("/")
        async def handler(db: AsyncSession = Depends(get_db)):
            ...
    """
    if _session_factory is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")

    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager variant for use outside FastAPI dependency injection."""
    if _session_factory is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")

    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_engine() -> AsyncEngine:
    """Return the raw engine (for migrations, health checks, etc.)."""
    if _engine is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    return _engine


async def check_db_health() -> dict:
    """
    Execute a simple query to verify database connectivity.
    Returns a dict suitable for health check responses.
    """
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            row = result.fetchone()
        return {"status": "healthy", "db": "connected", "result": row[0]}
    except Exception as exc:
        return {"status": "unhealthy", "db": "disconnected", "error": str(exc)}
