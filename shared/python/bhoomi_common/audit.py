"""
bhoomi_common.audit – Emit structured audit events to the audit service.

All data accesses and mutations MUST emit an audit event.
Events are written via the audit microservice (not directly to DB from here)
to ensure the append-only constraint is enforced at the service boundary.

Usage:
    from bhoomi_common.audit import emit_audit_event, AuditEventType

    await emit_audit_event(
        event_type=AuditEventType.PARCEL_VIEWED,
        actor=actor,
        resource_type="PARCEL",
        resource_id=parcel_id,
        parcel_id=parcel_id,
        purpose=actor.purpose,
        request=request,
    )
"""

from __future__ import annotations

import logging
import os
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

import httpx
from fastapi import Request

from bhoomi_common.auth import Actor

logger = logging.getLogger(__name__)

AUDIT_SERVICE_URL = os.environ.get(
    "AUDIT_SERVICE_URL", "http://audit:8000/api/v1/audit/events"
)


class AuditEventType(str, Enum):
    """Canonical audit event types."""
    # Parcel access
    PARCEL_VIEWED         = "PARCEL_VIEWED"
    PARCEL_SEARCHED       = "PARCEL_SEARCHED"
    PARCEL_EXPORTED       = "PARCEL_EXPORTED"
    PARCEL_CREATED        = "PARCEL_CREATED"
    PARCEL_UPDATED        = "PARCEL_UPDATED"
    PARCEL_MERGED         = "PARCEL_MERGED"
    PARCEL_SPLIT          = "PARCEL_SPLIT"

    # Record changes
    MUTATION_CREATED      = "MUTATION_CREATED"
    MUTATION_APPROVED     = "MUTATION_APPROVED"
    MUTATION_REJECTED     = "MUTATION_REJECTED"
    DEED_REGISTERED       = "DEED_REGISTERED"
    ENCUMBRANCE_ADDED     = "ENCUMBRANCE_ADDED"
    ENCUMBRANCE_RELEASED  = "ENCUMBRANCE_RELEASED"

    # Access control
    ACCESS_GRANTED        = "ACCESS_GRANTED"
    ACCESS_REVOKED        = "ACCESS_REVOKED"
    CONSENT_GIVEN         = "CONSENT_GIVEN"
    CONSENT_WITHDRAWN     = "CONSENT_WITHDRAWN"

    # Auth
    LOGIN                 = "LOGIN"
    LOGOUT                = "LOGOUT"
    TOKEN_REFRESHED       = "TOKEN_REFRESHED"

    # Bulk / admin
    BULK_EXPORT           = "BULK_EXPORT"
    SYNC_TRIGGERED        = "SYNC_TRIGGERED"
    SYSTEM_CONFIG_CHANGED = "SYSTEM_CONFIG_CHANGED"

    # ML / Trust
    CONFLICT_SCORE_COMPUTED  = "CONFLICT_SCORE_COMPUTED"
    CONFLICT_RESOLVED        = "CONFLICT_RESOLVED"
    TOPOLOGY_CONFLICT_FLAGGED = "TOPOLOGY_CONFLICT_FLAGGED"


async def emit_audit_event(
    event_type: AuditEventType | str,
    actor: Actor,
    resource_type: Optional[str] = None,
    resource_id: Optional[UUID] = None,
    parcel_id: Optional[UUID] = None,
    purpose: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> None:
    """
    Emit an audit event to the audit service (fire-and-forget with error logging).

    This function MUST NOT raise exceptions that would break the calling request –
    audit emission failure is logged but does not block the main operation.
    The audit service is responsible for durability guarantees.
    """
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    if request is not None:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

    event_data = {
        "event_type":     str(event_type),
        "actor_id":       actor.subject,
        "actor_role":     list(actor.roles)[0] if actor.roles else None,
        "resource_type":  resource_type,
        "resource_id":    str(resource_id) if resource_id else None,
        "parcel_id":      str(parcel_id) if parcel_id else None,
        "purpose":        purpose or actor.purpose,
        "ip_address":     ip_address,
        "session_id":     actor.session_id,
        "user_agent":     user_agent,
        "payload":        payload or {},
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(AUDIT_SERVICE_URL, json=event_data)
            if response.status_code not in (200, 201, 202):
                logger.warning(
                    "Audit service returned non-2xx status %d for event %s",
                    response.status_code,
                    event_type,
                )
    except httpx.RequestError as exc:
        # Log but never raise – audit emission must not break core operations
        logger.error(
            "Failed to emit audit event %s: %s (audit service may be down)",
            event_type,
            exc,
        )
    except Exception as exc:
        logger.exception("Unexpected error emitting audit event %s: %s", event_type, exc)
