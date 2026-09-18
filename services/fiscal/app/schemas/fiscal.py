from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime, date
import uuid
import decimal


class ProvenanceInfo(BaseModel):
    source_department: str
    source_system: str
    state_code: str = ""
    as_of_date: date
    data_freshness_status: Literal["LIVE", "CACHED", "SYNTHETIC", "DEMO"]
    last_synced_at: Optional[datetime] = None


class PropertyTaxResponse(BaseModel):
    id: uuid.UUID
    parcel_id: uuid.UUID
    assessment_year: int
    annual_value: Optional[decimal.Decimal]
    tax_amount: Optional[decimal.Decimal]
    arrears: Optional[decimal.Decimal]
    payment_status: Optional[str]
    last_payment_date: Optional[date]
    provenance: ProvenanceInfo
    coverage_note: str


class TaxDuesResponse(BaseModel):
    parcel_id: uuid.UUID
    total_outstanding: decimal.Decimal
    years_overdue: List[int]
    oldest_due_year: Optional[int]
    coverage_note: str
