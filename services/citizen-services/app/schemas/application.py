from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ApplicationType(str, Enum):
    MUTATION_REQUEST = "MUTATION_REQUEST"
    ENCUMBRANCE_CERTIFICATE = "ENCUMBRANCE_CERTIFICATE"
    LAND_USE_CHANGE_PERMISSION = "LAND_USE_CHANGE_PERMISSION"
    BUILDING_PERMIT = "BUILDING_PERMIT"
    PARCEL_BOUNDARY_CORRECTION = "PARCEL_BOUNDARY_CORRECTION"
    DISPUTE_FILING = "DISPUTE_FILING"


class ApplicationStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    ADDITIONAL_INFO_REQUESTED = "ADDITIONAL_INFO_REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"


class ApplicationCreate(BaseModel):
    application_type: ApplicationType
    parcel_id: uuid.UUID
    applicant_id: str = Field(..., description="Keycloak subject or citizen ID")
    details: Dict[str, Any] = Field(default_factory=dict, description="Application-specific payload")
    contact_mobile: Optional[str] = None
    contact_email: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    application_type: ApplicationType
    parcel_id: uuid.UUID
    applicant_id: str
    status: ApplicationStatus
    reference_number: str
    submitted_at: datetime
    last_updated: datetime
    details: Optional[Dict[str, Any]]
    remarks: Optional[str]

    class Config:
        from_attributes = True


class ApplicationListResponse(BaseModel):
    total: int
    items: List[ApplicationResponse]


SERVICE_CATALOG = [
    {
        "type": "MUTATION_REQUEST",
        "name": "Ownership Transfer (Mutation)",
        "description": "Transfer ownership or update record of rights after sale, inheritance, gift, or court order.",
        "required_documents": ["Sale deed / court order", "Identity proof", "Previous RoR copy"],
        "sla_days": 30,
        "fee_inr": 200,
    },
    {
        "type": "ENCUMBRANCE_CERTIFICATE",
        "name": "Encumbrance Certificate",
        "description": "Certified extract of all registered charges and transactions on a parcel.",
        "required_documents": ["Identity proof", "Survey number / ULPIN"],
        "sla_days": 3,
        "fee_inr": 50,
    },
    {
        "type": "LAND_USE_CHANGE_PERMISSION",
        "name": "Land Use Change Permission",
        "description": "Apply to convert agricultural land to non-agricultural use or change zoning category.",
        "required_documents": ["Site plan", "NOC from agriculture dept", "Identity proof"],
        "sla_days": 90,
        "fee_inr": 2000,
    },
    {
        "type": "BUILDING_PERMIT",
        "name": "Building Permit",
        "description": "Obtain construction permission for new buildings or extensions on registered parcels.",
        "required_documents": ["Architectural plan", "Structural certificate", "NOC from fire dept"],
        "sla_days": 60,
        "fee_inr": 5000,
    },
    {
        "type": "PARCEL_BOUNDARY_CORRECTION",
        "name": "Boundary Correction Request",
        "description": "Report and request correction for discrepancies in recorded parcel boundaries.",
        "required_documents": ["Survey sketch", "Neighbour consent", "GPS coordinates"],
        "sla_days": 45,
        "fee_inr": 100,
    },
    {
        "type": "DISPUTE_FILING",
        "name": "Dispute Filing",
        "description": "File a formal dispute for ownership, boundary, or land-use conflicts.",
        "required_documents": ["Statement of claim", "Supporting documents", "Advocate certification (optional)"],
        "sla_days": 0,  # Dispute resolution timeline varies
        "fee_inr": 0,
    },
]
