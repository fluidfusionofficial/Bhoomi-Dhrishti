from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime
import uuid


class TrustCheckResult(BaseModel):
    check_code: str
    check_name: str
    passed: bool
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    reason: str
    affected_departments: List[str]
    recommendation: str


class TrustScoreResponse(BaseModel):
    parcel_id: uuid.UUID
    trust_score: int
    risk_band: Literal["CLEAR", "LOW", "MEDIUM", "HIGH"]
    computed_at: datetime
    total_checks: int
    failed_checks_count: int
    checks: List[TrustCheckResult]
    failed_checks: List[TrustCheckResult]
    summary: str
    recommended_actions: List[str]
    method: str = "DETERMINISTIC_RULES"
