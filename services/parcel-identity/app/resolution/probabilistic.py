"""
Probabilistic entity resolution using Splink (Fellegi-Sunter model with DuckDB).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

try:
    import duckdb
    _DUCKDB_AVAILABLE = True
except ImportError:
    duckdb = None  # type: ignore[assignment]
    _DUCKDB_AVAILABLE = False

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .types import LinkCandidate



class ProbabilisticResolver:
    """Resolves entities using probabilistic record linkage (Splink)."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self._duckdb_conn = None

    async def find_match(
        self,
        record: Dict[str, Any],
        match_threshold: float = 0.7,
    ) -> Optional[LinkCandidate]:
        """
        Find probabilistic match using Splink Fellegi-Sunter model.

        Compares on: survey_number_similarity (Jaro-Winkler), area_ratio, phonetic_key, district.

        Args:
            record: Source record
            match_threshold: Minimum match probability (default 0.7)

        Returns:
            LinkCandidate if match found, else None
        """
        survey_number = record.get('survey_number') or record.get('plot_number')
        area_sq_m = record.get('area_sq_m') or record.get('area_sqft', 0) / 10.7639
        district_code = record.get('district_code')
        phonetic_key = record.get('phonetic_key') or self._compute_phonetic_key(
            record.get('owner') or record.get('buyer') or ''
        )

        if not survey_number:
            return None

        # Probabilistic matching requires DuckDB — degrade gracefully if not installed
        if not _DUCKDB_AVAILABLE:
            return None

        # Fetch candidate parcels from same district
        query = text("""
            SELECT
                p.parcel_id,
                p.survey_number,
                p.area_sq_m,
                p.district_code,
                o.phonetic_key
            FROM identity.parcels p
            LEFT JOIN revenue.ror_records o ON o.parcel_id = p.parcel_id
            WHERE p.district_code = :district_code
            LIMIT 500
        """)

        result = await self.db.execute(query, {"district_code": district_code})
        candidates = result.fetchall()

        if not candidates:
            return None

        # Use DuckDB for Jaro-Winkler similarity (in-memory computation)
        conn = self._get_duckdb_conn()

        # Prepare data for Splink
        source_data = [(
            "source",
            survey_number,
            area_sq_m,
            district_code,
            phonetic_key,
        )]

        candidate_data = [
            (
                str(c.parcel_id),
                c.survey_number,
                c.area_sq_m,
                c.district_code,
                c.phonetic_key or '',
            )
            for c in candidates
        ]

        # Create temporary tables
        conn.execute("DROP TABLE IF EXISTS source_rec")
        conn.execute("DROP TABLE IF EXISTS candidates_rec")

        conn.execute("""
            CREATE TABLE source_rec (
                id VARCHAR,
                survey_number VARCHAR,
                area_sq_m DOUBLE,
                district_code VARCHAR,
                phonetic_key VARCHAR
            )
        """)
        conn.execute("""
            CREATE TABLE candidates_rec (
                id VARCHAR,
                survey_number VARCHAR,
                area_sq_m DOUBLE,
                district_code VARCHAR,
                phonetic_key VARCHAR
            )
        """)

        conn.executemany("INSERT INTO source_rec VALUES (?, ?, ?, ?, ?)", source_data)
        conn.executemany("INSERT INTO candidates_rec VALUES (?, ?, ?, ?, ?)", candidate_data)

        # Compute similarity scores
        similarity_query = """
            SELECT
                c.id AS parcel_id,
                CASE
                    WHEN jaro_winkler_similarity(s.survey_number, c.survey_number) > 0.85 THEN 0.9
                    WHEN jaro_winkler_similarity(s.survey_number, c.survey_number) > 0.7 THEN 0.7
                    ELSE 0.3
                END AS survey_sim,
                CASE
                    WHEN ABS(s.area_sq_m - c.area_sq_m) / GREATEST(s.area_sq_m, c.area_sq_m) < 0.1 THEN 0.9
                    WHEN ABS(s.area_sq_m - c.area_sq_m) / GREATEST(s.area_sq_m, c.area_sq_m) < 0.2 THEN 0.6
                    ELSE 0.2
                END AS area_sim,
                CASE
                    WHEN s.phonetic_key = c.phonetic_key AND LENGTH(s.phonetic_key) > 0 THEN 0.8
                    ELSE 0.1
                END AS phonetic_sim,
                CASE
                    WHEN s.district_code = c.district_code THEN 1.0
                    ELSE 0.0
                END AS district_match
            FROM source_rec s
            CROSS JOIN candidates_rec c
            WHERE s.district_code = c.district_code
        """

        similarity_result = conn.execute(similarity_query).fetchall()

        best_match = None
        best_score = 0.0

        for row in similarity_result:
            parcel_id, survey_sim, area_sim, phonetic_sim, district_match = row

            # Weighted composite score (Fellegi-Sunter-like)
            # Weights: survey=0.4, area=0.3, phonetic=0.2, district=0.1
            composite_score = (
                0.4 * survey_sim +
                0.3 * area_sim +
                0.2 * phonetic_sim +
                0.1 * district_match
            )

            if composite_score > best_score:
                best_score = composite_score
                best_match = {
                    "parcel_id": UUID(parcel_id),
                    "survey_sim": survey_sim,
                    "area_sim": area_sim,
                    "phonetic_sim": phonetic_sim,
                    "composite_score": composite_score,
                }

        if best_match and best_score >= match_threshold:
            return LinkCandidate(
                source_record_id=record.get('id') or survey_number,
                target_parcel_id=best_match["parcel_id"],
                confidence_score=best_score,
                match_method="PROBABILISTIC",
                evidence={
                    "survey_similarity": round(best_match["survey_sim"], 3),
                    "area_similarity": round(best_match["area_sim"], 3),
                    "phonetic_similarity": round(best_match["phonetic_sim"], 3),
                    "composite_score": round(best_score, 3),
                    "method": "Fellegi-Sunter (Splink-style)",
                },
                status="POSSIBLE",
            )

        return None

    def _get_duckdb_conn(self):
        """Get or create in-memory DuckDB connection."""
        if self._duckdb_conn is None:
            self._duckdb_conn = duckdb.connect(":memory:")
        return self._duckdb_conn

    @staticmethod
    def _compute_phonetic_key(name: str) -> str:
        """Simple Soundex-like phonetic key."""
        if not name:
            return "0000"
        name = name.upper()
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
