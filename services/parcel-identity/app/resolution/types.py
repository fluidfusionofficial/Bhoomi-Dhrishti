"""
Shared dataclasses for resolution pipeline — kept in a separate module
to avoid circular imports between cascade.py and sub-resolvers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List
from uuid import UUID


@dataclass
class LinkCandidate:
    """A potential link between a source record and a canonical parcel."""
    source_record_id: str
    target_parcel_id: UUID
    confidence_score: float
    match_method: str  # SPATIAL, DETERMINISTIC, PROBABILISTIC, PHONETIC
    evidence: Dict[str, Any]
    status: str  # CONFIRMED, POSSIBLE, REQUIRES_REVIEW


@dataclass
class ResolutionResult:
    """Result of running the resolution cascade."""
    total_records: int
    matched: int
    possible_matches: int
    requires_review: int
    no_match: int
    links_created: List[LinkCandidate]
    duration_seconds: float
