from pydantic import BaseModel
from typing import Optional, List, Literal
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

RightType = Literal[
    "OWNERSHIP", "TENANCY", "SHARECROP", "OCCUPANCY",
    "BHOODAN", "INAM", "PORAMBOKE", "GOVERNMENT"
]
MutationStatus = Literal["PENDING", "APPROVED", "REJECTED"]
DataFreshness = Literal["LIVE", "CACHED", "SYNTHETIC", "DEMO"]


class ProvenanceInfo(BaseModel):
    source_department: str
    source_system: str
    state_code: str
    as_of_date: date
    data_freshness_status: DataFreshness
    last_synced_at: Optional[datetime] = None
    source_url: Optional[str] = None


class PartyResponse(BaseModel):
    id: UUID
    party_type: str
    name_en: str
    name_local: Optional[str] = None
    name_phonetic_key: Optional[str] = None

    model_config = {"from_attributes": True}


class RightDetail(BaseModel):
    id: UUID
    right_type: str
    party_id: Optional[UUID] = None
    party: Optional[PartyResponse] = None
    share_numerator: Optional[int] = None
    share_denominator: Optional[int] = None
    share_display: Optional[str] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None

    model_config = {"from_attributes": True}


class RecordOfRightsResponse(BaseModel):
    id: UUID
    parcel_id: UUID
    ror_id: Optional[str] = None
    record_date: Optional[date] = None
    survey_number: Optional[str] = None
    land_classification: Optional[str] = None
    land_use: Optional[str] = None
    area_sq_m: Optional[Decimal] = None
    area_native: Optional[Decimal] = None
    area_unit_native: Optional[str] = None
    rights: List[RightDetail] = []
    provenance: ProvenanceInfo
    coverage_note: str


class MutationResponse(BaseModel):
    id: UUID
    parcel_id: UUID
    mutation_type: str
    from_party_id: Optional[UUID] = None
    to_party_id: Optional[UUID] = None
    status: str
    officer_id: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    submitted_at: Optional[datetime] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class CreateMutationRequest(BaseModel):
    parcel_id: UUID
    mutation_type: str
    from_party_id: Optional[UUID] = None
    to_party_id: Optional[UUID] = None
    notes: Optional[str] = None


class ApproveMutationRequest(BaseModel):
    officer_id: str
    notes: Optional[str] = None


class RejectMutationRequest(BaseModel):
    officer_id: str
    rejection_reason: str
