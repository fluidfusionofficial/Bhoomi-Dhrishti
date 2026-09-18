"""
Phonetic entity resolution for owner name matching.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .types import LinkCandidate


class PhoneticResolver:
    """Resolves entities using phonetic name matching (Soundex-like)."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def find_match(
        self,
        record: Dict[str, Any],
        phonetic_threshold: float = 0.6,
    ) -> Optional[LinkCandidate]:
        """
        Find match using phonetic owner name comparison.

        Args:
            record: Source record with 'owner' or 'owners' field
            phonetic_threshold: Minimum confidence for match (default 0.6)

        Returns:
            LinkCandidate if match found, else None
        """
        owner_name = None
        if 'owner' in record:
            owner_name = record['owner']
        elif 'buyer' in record:
            owner_name = record['buyer']
        elif 'owners' in record and isinstance(record['owners'], list):
            if record['owners']:
                owner_name = record['owners'][0].get('name') or record['owners'][0].get('name_latin')

        if not owner_name:
            return None

        # Generate phonetic key
        phonetic_key = self._generate_phonetic_key(owner_name)

        # Query for matches on phonetic key
        query = text("""
            SELECT
                p.parcel_id,
                o.owner_name,
                o.phonetic_key,
                COUNT(*) OVER (PARTITION BY o.phonetic_key) AS num_matches
            FROM revenue.ror_records o
            JOIN identity.parcels p ON p.parcel_id = o.parcel_id
            WHERE o.phonetic_key = :phonetic_key
            LIMIT 10
        """)

        result = await self.db.execute(query, {"phonetic_key": phonetic_key})
        rows = result.fetchall()

        if not rows:
            return None

        # If multiple matches, lower confidence
        num_matches = rows[0].num_matches
        base_confidence = 0.8 if num_matches == 1 else 0.6 if num_matches <= 3 else 0.5

        # Also check for additional signals (survey number, district) to boost confidence
        survey_number = record.get('survey_number')
        district_code = record.get('district_code')

        best_match = None
        best_score = 0.0

        for row in rows:
            score = base_confidence

            # Boost if survey number or district also matches
            if survey_number:
                survey_check = await self.db.execute(
                    text("SELECT 1 FROM identity.parcels WHERE parcel_id = :pid AND survey_number = :sn"),
                    {"pid": row.parcel_id, "sn": survey_number}
                )
                if survey_check.fetchone():
                    score += 0.15

            if district_code:
                district_check = await self.db.execute(
                    text("SELECT 1 FROM identity.parcels WHERE parcel_id = :pid AND district_code = :dc"),
                    {"pid": row.parcel_id, "dc": district_code}
                )
                if district_check.fetchone():
                    score += 0.05

            if score > best_score:
                best_score = score
                best_match = row

        if best_match and best_score >= phonetic_threshold:
            return LinkCandidate(
                source_record_id=record.get('id') or record.get('survey_number', 'unknown'),
                target_parcel_id=best_match.parcel_id,
                confidence_score=min(best_score, 0.95),  # Cap at 0.95 for phonetic
                match_method="PHONETIC",
                evidence={
                    "phonetic_key": phonetic_key,
                    "matched_owner": best_match.owner_name,
                    "num_phonetic_matches": num_matches,
                    "confidence_boost": best_score - base_confidence,
                },
                status="POSSIBLE" if best_score < 0.8 else "CONFIRMED",
            )

        return None

    @staticmethod
    def _generate_phonetic_key(name: str) -> str:
        """Generate Soundex-like phonetic key."""
        if not name:
            return "0000"

        name = name.upper().strip()
        # Remove common prefixes/suffixes
        name = name.replace("MR.", "").replace("MRS.", "").replace("MS.", "").strip()

        if not name:
            return "0000"

        soundex_map = {
            'B': '1', 'F': '1', 'P': '1', 'V': '1',
            'C': '2', 'G': '2', 'J': '2', 'K': '2', 'Q': '2', 'S': '2', 'X': '2', 'Z': '2',
            'D': '3', 'T': '3',
            'L': '4',
            'M': '5', 'N': '5',
            'R': '6',
        }

        code = name[0]
        for char in name[1:]:
            if char in soundex_map:
                digit = soundex_map[char]
                if digit != code[-1]:
                    code += digit
            if len(code) >= 4:
                break

        code = (code + "000")[:4]
        return code
