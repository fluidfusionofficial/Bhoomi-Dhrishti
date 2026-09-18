"""
Pydantic v2 request/response schemas for the parcel-identity service.

These are the API contract — they intentionally differ from the ORM models
so that the DB schema can evolve independently of the API surface.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------

class ProvenanceInfo(BaseModel):
    """Mandatory provenance block on every API response."""
    source_department: str
    source_system: str
    state_code: str
    as_of_date: date
    data_freshness_status: Literal["LIVE", "CACHED", "SYNTHETIC", "DEMO"]
    last_synced_at: Optional[datetime] = None

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Lineage
# ---------------------------------------------------------------------------

class ParcelLineageEvent(BaseModel):
    id: uuid.UUID
    # SUBDIVISION | AMALGAMATION | BOUNDARY_CORRECTION | RESURVEY_RENUMBER
    event_type: str
    parent_parcel_id: Optional[uuid.UUID] = None
    child_parcel_id: Optional[uuid.UUID] = None
    event_date: date
    authorising_document: Optional[str] = None
    authorising_authority: Optional[str] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class LineageTree(BaseModel):
    """Returned by GET /api/v1/parcels/{id}/lineage."""
    parcel: "ParcelIdentityResponse"
    parents: List[ParcelLineageEvent] = Field(default_factory=list)
    children: List[ParcelLineageEvent] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Aliases
# ---------------------------------------------------------------------------

class ParcelAlias(BaseModel):
    alias_type: str
    alias_value: str
    source_system: Optional[str] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None

    model_config = {"from_attributes": True}


class ParcelAliasResponse(BaseModel):
    parcel_id: uuid.UUID
    aliases: List[ParcelAlias] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Core parcel identity
# ---------------------------------------------------------------------------

class ParcelIdentityResponse(BaseModel):
    """
    Full parcel identity response — every field that callers may depend on.

    ulpin_is_authoritative: True when the ULPIN has been set on this record
    (indicating it was assigned by a DILRMP/state authority and stored here
    via the promote-ulpin workflow).
    """
    id: uuid.UUID
    bdpr: str
    ulpin: Optional[str] = None
    ulpin_is_authoritative: bool
    state_code: str
    district_code: str
    subdistrict_code: Optional[str] = None
    village_code: Optional[str] = None
    urban_ward_code: Optional[str] = None
    is_urban: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    system_of_record_flag: str
    provenance: ProvenanceInfo

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class CreateParcelRequest(BaseModel):
    state_code: str = Field(..., min_length=2, max_length=10)
    district_code: str = Field(..., min_length=2, max_length=10)
    subdistrict_code: Optional[str] = Field(None, max_length=10)
    village_code: Optional[str] = Field(None, max_length=10)
    urban_ward_code: Optional[str] = Field(None, max_length=10)
    is_urban: bool = False
    initial_survey_number: Optional[str] = Field(None, max_length=200)


class PromoteUlpinRequest(BaseModel):
    ulpin: str = Field(..., min_length=10, max_length=20)
    ulpin_source: str = Field(..., min_length=1, max_length=100)
    ulpin_assigned_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

class ParcelSearchResult(BaseModel):
    """Compact parcel entry in search result lists."""
    id: uuid.UUID
    bdpr: str
    ulpin: Optional[str] = None
    state_code: str
    district_code: str
    subdistrict_code: Optional[str] = None
    village_code: Optional[str] = None
    is_urban: bool
    is_active: bool
    system_of_record_flag: str

    model_config = {"from_attributes": True}


class ParcelSearchResponse(BaseModel):
    items: List[ParcelSearchResult]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Error helpers
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    code: str
    message: str
    field: Optional[str] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
    request_id: Optional[str] = None


# Resolve forward reference
LineageTree.model_rebuild()
