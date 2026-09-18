"""
bhoomi_common.errors – Standard error responses and exception handlers.

Register these handlers in each FastAPI service's main.py:

    from bhoomi_common.errors import register_exception_handlers
    register_exception_handlers(app)
"""

from __future__ import annotations

import logging
import traceback
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Custom exception classes
# ─────────────────────────────────────────────────────────────────────────────

class BhoomiBadRequest(Exception):
    """400 – Invalid request parameters."""
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)


class BhoomiNotFound(Exception):
    """404 – Requested resource does not exist."""
    def __init__(self, resource: str, id: Any = None):
        self.resource = resource
        self.id = id
        super().__init__(f"{resource} not found: {id}")


class BhoomiConflict(Exception):
    """409 – Resource conflict (duplicate, concurrent update, etc.)."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class BhoomiForbidden(Exception):
    """403 – Insufficient permissions for this operation."""
    def __init__(self, message: str = "Insufficient permissions"):
        self.message = message
        super().__init__(message)


class BhoomiProvenanceError(Exception):
    """422 – Record lacks required provenance fields."""
    def __init__(self, missing_fields: list[str]):
        self.missing_fields = missing_fields
        super().__init__(f"Missing provenance fields: {missing_fields}")


class BhoomiUpstreamError(Exception):
    """502 – Upstream source system unavailable or returned an error."""
    def __init__(self, source_system: str, detail: str):
        self.source_system = source_system
        self.detail = detail
        super().__init__(f"Upstream error from {source_system}: {detail}")


# ─────────────────────────────────────────────────────────────────────────────
# Response builders
# ─────────────────────────────────────────────────────────────────────────────

def _error_response(
    status_code: int,
    error: str,
    message: str,
    details: Optional[list] = None,
    trace_id: Optional[str] = None,
) -> JSONResponse:
    body: Dict[str, Any] = {
        "error":     error,
        "message":   message,
        "trace_id":  trace_id or str(uuid4()),
    }
    if details:
        body["details"] = details
    return JSONResponse(status_code=status_code, content=body)


# ─────────────────────────────────────────────────────────────────────────────
# Exception handlers
# ─────────────────────────────────────────────────────────────────────────────

async def _handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    return _error_response(
        status_code=exc.status_code,
        error="HTTP_ERROR",
        message=str(exc.detail),
    )


async def _handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {"field": ".".join(str(loc) for loc in e["loc"]), "message": e["msg"]}
        for e in exc.errors()
    ]
    return _error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error="VALIDATION_ERROR",
        message="Request validation failed",
        details=details,
    )


async def _handle_not_found(request: Request, exc: BhoomiNotFound) -> JSONResponse:
    return _error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        error="NOT_FOUND",
        message=f"{exc.resource} not found" + (f": {exc.id}" if exc.id else ""),
    )


async def _handle_bad_request(request: Request, exc: BhoomiBadRequest) -> JSONResponse:
    details = [{"field": exc.field, "message": exc.message}] if exc.field else None
    return _error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        error="BAD_REQUEST",
        message=exc.message,
        details=details,
    )


async def _handle_conflict(request: Request, exc: BhoomiConflict) -> JSONResponse:
    return _error_response(
        status_code=status.HTTP_409_CONFLICT,
        error="CONFLICT",
        message=exc.message,
    )


async def _handle_forbidden(request: Request, exc: BhoomiForbidden) -> JSONResponse:
    return _error_response(
        status_code=status.HTTP_403_FORBIDDEN,
        error="FORBIDDEN",
        message=exc.message,
    )


async def _handle_provenance_error(request: Request, exc: BhoomiProvenanceError) -> JSONResponse:
    return _error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error="PROVENANCE_MISSING",
        message="Record is missing required provenance fields",
        details=[{"field": f, "message": "Required provenance field missing"} for f in exc.missing_fields],
    )


async def _handle_upstream_error(request: Request, exc: BhoomiUpstreamError) -> JSONResponse:
    return _error_response(
        status_code=status.HTTP_502_BAD_GATEWAY,
        error="UPSTREAM_ERROR",
        message=f"Source system '{exc.source_system}' is unavailable: {exc.detail}",
    )


async def _handle_unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
    trace_id = str(uuid4())
    logger.exception("Unhandled exception [trace_id=%s]: %s", trace_id, exc)
    return _error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred. Please contact support with the trace ID.",
        trace_id=trace_id,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all Bhoomi exception handlers on a FastAPI application."""
    app.add_exception_handler(HTTPException,            _handle_http_exception)       # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError,   _handle_validation_error)     # type: ignore[arg-type]
    app.add_exception_handler(BhoomiNotFound,           _handle_not_found)            # type: ignore[arg-type]
    app.add_exception_handler(BhoomiBadRequest,         _handle_bad_request)          # type: ignore[arg-type]
    app.add_exception_handler(BhoomiConflict,           _handle_conflict)             # type: ignore[arg-type]
    app.add_exception_handler(BhoomiForbidden,          _handle_forbidden)            # type: ignore[arg-type]
    app.add_exception_handler(BhoomiProvenanceError,    _handle_provenance_error)     # type: ignore[arg-type]
    app.add_exception_handler(BhoomiUpstreamError,      _handle_upstream_error)       # type: ignore[arg-type]
    app.add_exception_handler(Exception,                _handle_unhandled_exception)  # type: ignore[arg-type]
