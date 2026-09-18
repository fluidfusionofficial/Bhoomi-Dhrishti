"""
bhoomi_common.models – Base Pydantic models with provenance and confidence fields.

Every API response model that wraps a database record MUST inherit from
ProvenanceBase to ensure the provenance contract is enforced at the
serialisation boundary.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field, field_validator, model_validator


# ─────────────────────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────────────────────

class DataFreshnessStatus(str, Enum):
    """Provenance freshness classification for every sourced record."""
    LIVE      = "LIVE"       # Pulled live from source system API in this request
    CACHED    = "CACHED"     # From last successful sync (timestamp in source_as_of_date)
    SYNTHETIC = "SYNTHETIC"  # Demo / generated data – never present in production


class SystemOfRecordFlag(str, Enum):
    """Indicates the authoritative status of a parcel identity record."""
    AUTHORITATIVE = "AUTHORITATIVE"  # This platform IS the system of record
    DERIVED       = "DERIVED"        # Derived from a state system; may lag
    CACHE         = "CACHE"          # Transient copy; should be refreshed


class AccuracyClass(str, Enum):
    """Spatial accuracy classification for parcel geometries."""
    A       = "A"        # Sub-metre (CORS / Total Station)
    B       = "B"        # 1–5 m (DGPS / ETS)
    C       = "C"        # 5–20 m (GPS / satellite georeferencing)
    D       = "D"        # > 20 m (digitised from unrectified maps)
    UNKNOWN = "UNKNOWN"  # Accuracy not assessed


class RiskBand(str, Enum):
    """ML-computed risk band for conflict scoring."""
    HIGH       = "HIGH"
    MEDIUM     = "MEDIUM"
    LOW        = "LOW"
    NEGLIGIBLE = "NEGLIGIBLE"


class Confidence(str, Enum):
    """Confidence level for inferred linkages (e.g. dispute-to-parcel)."""
    POSSIBLE   = "POSSIBLE"    # Inferred; requires human verification
    CONFIRMED  = "CONFIRMED"   # Manually verified
    RULED_OUT  = "RULED_OUT"   # Explicitly excluded


# ─────────────────────────────────────────────────────────────────────────────
# Common field definitions
# ─────────────────────────────────────────────────────────────────────────────

class BhoomiBased(BaseModel):
    """Minimal base with forbid extra fields and populated-by-name defaults."""
    model_config = {"populate_by_name": True, "extra": "forbid", "use_enum_values": True}


class TimestampMixin(BaseModel):
    """Adds standard created_at / updated_at timestamps."""
    created_at: Optional[datetime] = Field(None, description="Record creation timestamp (UTC)")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp (UTC)")


class ProvenanceBase(BhoomiBased):
    """
    MANDATORY provenance fields – must be present on every API response
    that wraps a sourced database record.

    These fields answer the question: "Where did this data come from,
    how recent is it, and how confident are we in its accuracy?"
    """
    source_department: str = Field(
        ...,
        description="Government department that owns the source record (e.g. 'TN Revenue Department')",
        max_length=100,
    )
    source_system: str = Field(
        ...,
        description="Source IT system identifier (e.g. 'TN_BHOOMI', 'NGDRS', 'SVAMITVA')",
        max_length=100,
    )
    source_as_of_date: date = Field(
        ...,
        description="The date on which the source record was last confirmed accurate",
    )
    data_freshness_status: DataFreshnessStatus = Field(
        DataFreshnessStatus.CACHED,
        description="How fresh is this data? LIVE = just fetched; CACHED = from last sync; SYNTHETIC = demo",
    )
    last_synced_at: Optional[datetime] = Field(
        None,
        description="When this platform last successfully synced with the source system",
    )

    @field_validator("source_as_of_date")
    @classmethod
    def source_date_not_future(cls, v: date) -> date:
        from datetime import date as date_t
        if v > date_t.today():
            raise ValueError("source_as_of_date cannot be in the future")
        return v


# ─────────────────────────────────────────────────────────────────────────────
# Parcel identity models
# ─────────────────────────────────────────────────────────────────────────────

class ParcelBase(BhoomiBased):
    """Minimal parcel fields shared across create/update/response."""
    bdpr: str = Field(..., description="Bhoomi Dhrishti Parcel Reference (BD-<STATE>-<SEQ>)", pattern=r"^BD-[A-Z]{2}-\d{7}$")
    ulpin: Optional[str] = Field(None, description="ULPIN (20-char national identifier from DILRMP)")
    state_code: str = Field(..., description="LGD state code", max_length=10)
    district_code: str = Field(..., description="LGD district code", max_length=10)
    is_urban: bool = Field(False, description="True for urban parcels (ward-based); False for rural (village-based)")
    system_of_record_flag: SystemOfRecordFlag = Field(SystemOfRecordFlag.DERIVED)


class ParcelResponse(ParcelBase, TimestampMixin):
    """Full parcel response model."""
    id: uuid.UUID
    subdistrict_code: Optional[str] = None
    village_code: Optional[str] = None
    urban_ward_code: Optional[str] = None
    is_active: bool = True

    model_config = {"from_attributes": True, "populate_by_name": True, "use_enum_values": True}


class ParcelSummaryResponse(BhoomiBased):
    """Compact parcel summary (used in list views and search results)."""
    id: uuid.UUID
    bdpr: str
    ulpin: Optional[str] = None
    state_code: str
    district_code: str
    is_urban: bool
    area_sq_m: Optional[float] = None
    accuracy_class: Optional[AccuracyClass] = None
    risk_band: Optional[RiskBand] = None
    conflict_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    open_topology_conflicts: int = 0
    active_encumbrances: int = 0
    active_disputes: int = 0

    model_config = {"from_attributes": True, "use_enum_values": True}


# ─────────────────────────────────────────────────────────────────────────────
# Geometry model
# ─────────────────────────────────────────────────────────────────────────────

class GeometryResponse(BhoomiBased):
    """GeoJSON-compatible geometry wrapper."""
    type: str
    coordinates: Any  # GeoJSON coordinate arrays

    model_config = {"extra": "allow"}


class ParcelGeometryResponse(BhoomiBased):
    """Parcel geometry with provenance."""
    id: uuid.UUID
    parcel_id: uuid.UUID
    geometry: GeometryResponse
    accuracy_class: AccuracyClass
    area_sq_m: Optional[float] = None
    source_survey_date: Optional[date] = None
    version_number: int = 1
    is_active: bool = True
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True, "use_enum_values": True}


# ─────────────────────────────────────────────────────────────────────────────
# Conflict / trust score model
# ─────────────────────────────────────────────────────────────────────────────

class ConflictScoreResponse(BhoomiBased):
    """ML conflict score for a parcel."""
    id: uuid.UUID
    parcel_id: uuid.UUID
    score_type: str
    score_value: float = Field(..., ge=0.0, le=1.0)
    risk_band: RiskBand
    percentile_rank: Optional[float] = Field(None, ge=0, le=100)
    method: Optional[str] = None
    contributing_factors: Optional[Dict[str, Any]] = None
    computed_at: datetime
    model_version: Optional[str] = None

    model_config = {"from_attributes": True, "use_enum_values": True}


# ─────────────────────────────────────────────────────────────────────────────
# Land passport (citizen-facing aggregated view)
# ─────────────────────────────────────────────────────────────────────────────

class LandPassportResponse(BhoomiBased):
    """
    Digital Land Passport – aggregated view of all known facts about a parcel.
    Presented to citizens via the citizen-services API.

    IMPORTANT: Each section carries its own provenance. The top-level
    overall_freshness is the WORST (most stale) freshness across all sections.
    """
    parcel: ParcelSummaryResponse
    geometry: Optional[ParcelGeometryResponse] = None
    rights_summary: Optional[str] = Field(
        None,
        description="Human-readable ownership summary (e.g. '2/3 share: Ramu S/o Krishnan; 1/3 share: Devi W/o Ramu')"
    )
    encumbrances_count: int = 0
    active_disputes: bool = False
    conflict_score: Optional[ConflictScoreResponse] = None
    overall_freshness: DataFreshnessStatus = DataFreshnessStatus.CACHED
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True, "use_enum_values": True}


# ─────────────────────────────────────────────────────────────────────────────
# Pagination
# ─────────────────────────────────────────────────────────────────────────────

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated API response envelope."""
    items: List[T]
    total: Optional[int] = Field(None, description="Total count (may be omitted for cursor pagination)")
    page: Optional[int] = None
    page_size: int
    next_cursor: Optional[str] = Field(None, description="Opaque cursor for next page (cursor pagination)")
    has_next: bool = False

    model_config = {"arbitrary_types_allowed": True}


# ─────────────────────────────────────────────────────────────────────────────
# Standard error envelope
# ─────────────────────────────────────────────────────────────────────────────

class ErrorDetail(BhoomiBased):
    field: Optional[str] = None
    message: str


class ErrorResponse(BhoomiBased):
    """Standard error response body for all Bhoomi Dhrishti APIs."""
    error: str = Field(..., description="Machine-readable error code (UPPER_SNAKE_CASE)")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[List[ErrorDetail]] = None
    trace_id: Optional[str] = Field(None, description="Request trace ID for log correlation")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
