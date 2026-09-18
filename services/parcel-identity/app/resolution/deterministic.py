"""
Deterministic entity resolution via normalized key matching.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .types import LinkCandidate


class DeterministicResolver:
    """Resolves entities using normalized deterministic keys."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def find_match(self, record: Dict[str, Any]) -> Optional[LinkCandidate]:
        """
        Find exact match after normalizing survey number + district + village.

        Args:
            record: Source record with 'survey_number', 'district_code', 'village_code'

        Returns:
            LinkCandidate if match found, else None
        """
        survey_number = record.get('survey_number') or record.get('plot_number')
        district_code = record.get('district_code')
        village_code = record.get('village_code')

        if not survey_number:
            return None

        # Normalize survey number (strip leading zeros, remove separators)
        survey_normalized = self._normalize_survey_number(survey_number)

        # Query for exact match on normalized keys
        query = text("""
            SELECT
                p.parcel_id,
                pa.alias_value AS matched_survey_number
            FROM identity.parcels p
            LEFT JOIN identity.parcel_aliases pa
                ON pa.parcel_id = p.parcel_id
                AND pa.alias_type = 'SURVEY_NUMBER'
            WHERE
                (
                    REGEXP_REPLACE(p.survey_number, '[^A-Za-z0-9]', '', 'g') = :survey_normalized
                    OR REGEXP_REPLACE(pa.alias_value, '[^A-Za-z0-9]', '', 'g') = :survey_normalized
                )
                AND (:district_code IS NULL OR p.district_code = :district_code)
                AND (:village_code IS NULL OR p.village_code = :village_code)
            LIMIT 1
        """)

        result = await self.db.execute(query, {
            "survey_normalized": survey_normalized,
            "district_code": district_code,
            "village_code": village_code,
        })
        row = result.fetchone()

        if row:
            return LinkCandidate(
                source_record_id=record.get('id') or survey_number,
                target_parcel_id=row.parcel_id,
                confidence_score=1.0,  # Deterministic match
                match_method="DETERMINISTIC",
                evidence={
                    "matched_survey_number": row.matched_survey_number or survey_number,
                    "normalized_key": survey_normalized,
                    "district_code": district_code,
                    "village_code": village_code,
                },
                status="CONFIRMED",
            )

        return None

    @staticmethod
    def _normalize_survey_number(survey: str) -> str:
        """Normalize survey number: remove separators, leading zeros, uppercase."""
        # Remove all non-alphanumeric
        normalized = re.sub(r'[^A-Za-z0-9]', '', survey)
        # Strip leading zeros from numeric parts
        parts = re.split(r'(\d+)', normalized)
        normalized_parts = [part.lstrip('0') or '0' if part.isdigit() else part for part in parts]
        return ''.join(normalized_parts).upper()
