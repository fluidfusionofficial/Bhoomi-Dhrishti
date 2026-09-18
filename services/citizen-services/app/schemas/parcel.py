"""
Tiered disclosure schemas for parcel profile endpoint.
Each tier returns progressively more detail.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


# --------------------------------------------------------------------------
# Public tier (no auth required)
# --------------------------------------------------------------------------
class PublicParcelProfile(BaseModel):
    parcel_id: uuid.UUID
    ulpin: Optional[str]
    area_sq_m: Optional[float]
    land_use: Optional[str]
    geometry: Optional[Dict[str, Any]]   # GeoJSON shape only
    is_urban: bool
    encumbered: bool           # boolean only — no amount/holder
    has_dispute: bool          # boolean only — no case details


# --------------------------------------------------------------------------
# Authenticated citizen (viewing own parcel)
# --------------------------------------------------------------------------
class RightEntry(BaseModel):
    right_type: str
    holder_name: str           # Citizen's own name — allowed
    share: Optional[str]


class EncumbranceEntry(BaseModel):
    encumbrance_type: str
    holder_name: str = "Financial Institution"   # always masked
    amount: Optional[float]
    is_active: bool


class DisputeEntry(BaseModel):
    case_number: str
    status: str


class DeedEntry(BaseModel):
    deed_type: str
    registration_date: Optional[str]
    consideration_amount: Optional[float]


class CitizenOwnParcelProfile(PublicParcelProfile):
    rights: List[RightEntry] = []
    encumbrances: List[EncumbranceEntry] = []
    disputes: List[DisputeEntry] = []
    own_deeds: List[DeedEntry] = []


# --------------------------------------------------------------------------
# Officer / Revenue Officer (full detail, no masking)
# --------------------------------------------------------------------------
class ConflictEntry(BaseModel):
    score_type: str
    risk_band: str
    score_value: float
    contributing_factors: Optional[Dict[str, Any]]


class OfficerParcelProfile(CitizenOwnParcelProfile):
    state_code: Optional[str]
    district_code: Optional[str]
    village_code: Optional[str]
    bdpr: Optional[str]
    all_rights: List[RightEntry] = []         # All holders, unmasked
    all_encumbrances: List[EncumbranceEntry] = []
    all_deeds: List[DeedEntry] = []
    conflict_scores: List[ConflictEntry] = []
    pending_mutation_count: int = 0
    data_freshness_status: Optional[str]
