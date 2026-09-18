from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


AUDIT_EVENT_TYPES = [
    "PARCEL_VIEWED",
    "PARCEL_SEARCHED",
    "ROR_VIEWED",
    "DEED_VIEWED",
    "ENCUMBRANCE_CHECKED",
    "MUTATION_SUBMITTED",
    "MUTATION_APPROVED",
    "MUTATION_REJECTED",
    "BUILDING_PERMIT_APPLIED",
    "CONFLICT_REVIEWED",
    "CONFLICT_ADJUDICATED",
    "ML_SCORE_ACCESSED",
    "DATA_EXPORT",
    "INTEGRATION_SYNC",
    "ACCESS_TOKEN_ISSUED",
    "USER_LOGIN",
    "USER_LOGOUT",
]


class AuditEventCreate(BaseModel):
    event_type: str = Field(..., description="One of AUDIT_EVENT_TYPES")
    actor_id: str = Field(..., description="Keycloak subject or system identity")
    actor_role: str = Field(..., description="e.g. CITIZEN, REVENUE_OFFICER, ADMIN")
    actor_org: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    parcel_id: Optional[uuid.UUID] = None
    purpose: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditEventResponse(BaseModel):
    id: uuid.UUID
    event_time: datetime
    event_type: str
    actor_id: str
    actor_role: str
    actor_org: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    parcel_id: Optional[uuid.UUID]
    purpose: Optional[str]
    payload: Optional[Dict[str, Any]]
    event_hash: Optional[str]

    class Config:
        from_attributes = True


class AuditEventPage(BaseModel):
    total: int
    items: List[AuditEventResponse]


class CitizenAccessEvent(BaseModel):
    """Tiered disclosure view — never exposes officer name."""
    date: str                       # YYYY-MM-DD
    accessor_role: str              # e.g. "Registration Officer"
    organization: Optional[str]
    purpose: Optional[str]
    access_count: int


class CitizenAccessResponse(BaseModel):
    parcel_id: uuid.UUID
    ulpin: Optional[str]
    events: List[CitizenAccessEvent]


class IntegrityReport(BaseModel):
    verified: bool
    total_events: int
    broken_at: Optional[uuid.UUID] = None
    broken_position: Optional[int] = None
    message: str


class AuditSearchParams(BaseModel):
    actor_id: Optional[str] = None
    actor_role: Optional[str] = None
    event_type: Optional[str] = None
    parcel_id: Optional[uuid.UUID] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = 1
    page_size: int = 50
