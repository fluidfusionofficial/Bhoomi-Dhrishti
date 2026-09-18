from pydantic import BaseModel
from typing import Optional, List, Literal, Any, Dict
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

DataFreshness = Literal["LIVE", "CACHED", "SYNTHETIC", "DEMO"]


class ProvenanceInfo(BaseModel):
    source_department: str
    source_system: str
    state_code: str
    as_of_date: date
    data_freshness_status: DataFreshness
    last_synced_at: Optional[datetime] = None
    source_url: Optional[str] = None


class PartyRef(BaseModel):
    id: UUID
    name_en: str
    name_local: Optional[str] = None
    party_type: Optional[str] = None

    model_config = {"from_attributes": True}


class DeedResponse(BaseModel):
    id: UUID
    parcel_id: UUID
    deed_number: Optional[str] = None
    deed_type: Optional[str] = None
    sro_code: Optional[str] = None
    registration_date: Optional[date] = None
    consideration_amount: Optional[Decimal] = None
    seller: Optional[PartyRef] = None
    buyer: Optional[PartyRef] = None
    provenance: ProvenanceInfo

    model_config = {"from_attributes": True}


class EncumbranceResponse(BaseModel):
    id: UUID
    parcel_id: UUID
    encumbrance_type: str
    in_favour_of_party_id: Optional[UUID] = None
    in_favour_of: Optional[PartyRef] = None
    is_active: bool
    amount: Optional[Decimal] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    model_config = {"from_attributes": True}


class EncumbranceCertificateResponse(BaseModel):
    parcel_id: UUID
    period_from: Optional[date] = None
    period_to: Optional[date] = None
    total_deeds: int
    active_encumbrances: int
    encumbrances: List[EncumbranceResponse]
    deeds_summary: List[Dict[str, Any]]
    sources_checked: List[str]
    last_synced_at: datetime
    provenance: ProvenanceInfo
    coverage_note: str


class DuplicateCheckRequest(BaseModel):
    parcel_id: UUID


class DuplicateCheckResponse(BaseModel):
    parcel_id: UUID
    has_duplicate_flag: bool
    flags: List[Dict[str, Any]]
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    checked_at: datetime
    sources_checked: List[str]
    provenance: ProvenanceInfo
