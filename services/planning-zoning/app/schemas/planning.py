from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime, date
import uuid
import decimal


class ProvenanceInfo(BaseModel):
    source_department: str
    source_system: str
    as_of_date: date
    data_freshness_status: Literal["LIVE", "CACHED", "SYNTHETIC", "DEMO"]
    last_synced_at: Optional[datetime] = None


class ZoneResponse(BaseModel):
    id: uuid.UUID
    parcel_id: uuid.UUID
    zone_code: Optional[str]
    zone_type: Optional[str]
    fsi_allowed: Optional[decimal.Decimal]
    ground_coverage_pct: Optional[decimal.Decimal]
    max_height_m: Optional[decimal.Decimal]
    master_plan_year: Optional[int]
    provenance: ProvenanceInfo


class BuildingPermissionResponse(BaseModel):
    id: uuid.UUID
    parcel_id: uuid.UUID
    permission_number: Optional[str]
    permission_type: Optional[str]
    status: Optional[str]
    applied_date: Optional[date]
    approved_date: Optional[date]
    floor_count: Optional[int]
    approved_area_sq_m: Optional[decimal.Decimal]
    provenance: ProvenanceInfo


class DisputeResponse(BaseModel):
    id: uuid.UUID
    parcel_id: uuid.UUID
    case_number: Optional[str]
    court: Optional[str]
    case_type: Optional[str]
    status: Optional[str]
    filed_date: Optional[date]
    parties_description: Optional[str]
    confidence: str  # POSSIBLE | CONFIRMED — NEVER drop this field
    linkage_method: Optional[str]
    # Always explain HOW the case was linked to this parcel
    linkage_note: str
