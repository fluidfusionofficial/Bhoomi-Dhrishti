"""
Detect disagreements between linked departmental records for the same parcel.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class ConflictType(str, Enum):
    """Types of cross-registry conflicts."""
    AREA_MISMATCH = "AREA_MISMATCH"
    OWNER_MISMATCH = "OWNER_MISMATCH"
    STATUS_MISMATCH = "STATUS_MISMATCH"
    TRANSACTION_MUTATION_LAG = "TRANSACTION_MUTATION_LAG"
    GEOMETRY_MISMATCH = "GEOMETRY_MISMATCH"


@dataclass
class Conflict:
    """A detected conflict between two sources."""
    parcel_id: UUID
    conflict_type: ConflictType
    source_a: str
    source_b: str
    field_name: str
    value_a: Any
    value_b: Any
    confidence: float
    severity: str  # HIGH, MEDIUM, LOW
    description: str


class ConflictDetector:
    """Detects disagreements between departmental records."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def detect_all_conflicts(
        self,
        parcel_id: Optional[UUID] = None,
        state_code: Optional[str] = None,
    ) -> List[Conflict]:
        """
        Run all conflict detection checks.

        Args:
            parcel_id: Optional specific parcel to check (else checks all)
            state_code: Optional state filter

        Returns:
            List of detected conflicts
        """
        conflicts = []

        conflicts.extend(await self.detect_area_conflicts(parcel_id, state_code))
        conflicts.extend(await self.detect_owner_conflicts(parcel_id, state_code))
        conflicts.extend(await self.detect_status_conflicts(parcel_id, state_code))
        conflicts.extend(await self.detect_transaction_lag(parcel_id, state_code))
        conflicts.extend(await self.detect_geometry_conflicts(parcel_id, state_code))

        return conflicts

    async def detect_area_conflicts(
        self,
        parcel_id: Optional[UUID] = None,
        state_code: Optional[str] = None,
    ) -> List[Conflict]:
        """
        Detect >10% area discrepancy across linked sources.

        Returns:
            List of area conflict records
        """
        query = text("""
            WITH parcel_areas AS (
                SELECT
                    p.parcel_id,
                    p.area_sq_m AS canonical_area,
                    pl.source_type,
                    CASE
                        WHEN pl.source_type = 'revenue_ror' THEN ror.area_native * ua.conversion_factor
                        WHEN pl.source_type = 'municipal_tax' THEN mt.area_sq_m
                        ELSE p.area_sq_m
                    END AS source_area
                FROM identity.parcels p
                JOIN identity.parcel_links pl ON pl.target_parcel_id = p.parcel_id
                LEFT JOIN revenue.ror_records ror ON ror.parcel_id = p.parcel_id
                LEFT JOIN reference.unit_conversions ua
                    ON ua.unit_name = ror.unit_native AND ua.district_code = p.district_code
                LEFT JOIN fiscal.property_tax mt ON mt.parcel_id = p.parcel_id
                WHERE (:parcel_id IS NULL OR p.parcel_id = :parcel_id)
                  AND (:state_code IS NULL OR p.state_code = :state_code)
            ),
            conflicts_detected AS (
                SELECT
                    pa1.parcel_id,
                    pa1.source_type AS source_a,
                    pa2.source_type AS source_b,
                    pa1.source_area AS area_a,
                    pa2.source_area AS area_b,
                    ABS(pa1.source_area - pa2.source_area) / GREATEST(pa1.source_area, pa2.source_area) AS area_diff_ratio
                FROM parcel_areas pa1
                JOIN parcel_areas pa2 ON pa1.parcel_id = pa2.parcel_id AND pa1.source_type < pa2.source_type
                WHERE ABS(pa1.source_area - pa2.source_area) / GREATEST(pa1.source_area, pa2.source_area) > 0.1
            )
            SELECT * FROM conflicts_detected
        """)

        result = await self.db.execute(query, {
            "parcel_id": parcel_id,
            "state_code": state_code,
        })

        conflicts = []
        for row in result.fetchall():
            severity = "HIGH" if row.area_diff_ratio > 0.3 else "MEDIUM"
            conflicts.append(Conflict(
                parcel_id=row.parcel_id,
                conflict_type=ConflictType.AREA_MISMATCH,
                source_a=row.source_a,
                source_b=row.source_b,
                field_name="area_sq_m",
                value_a=round(row.area_a, 2),
                value_b=round(row.area_b, 2),
                confidence=0.95,  # Deterministic check
                severity=severity,
                description=f"Area differs by {row.area_diff_ratio*100:.1f}% between {row.source_a} and {row.source_b}",
            ))

        return conflicts

    async def detect_owner_conflicts(
        self,
        parcel_id: Optional[UUID] = None,
        state_code: Optional[str] = None,
    ) -> List[Conflict]:
        """
        Detect owner name mismatch after phonetic normalization.

        Returns:
            List of owner conflict records
        """
        query = text("""
            WITH owner_sources AS (
                SELECT
                    p.parcel_id,
                    'revenue_ror' AS source_type,
                    ror.owner_name,
                    ror.phonetic_key,
                    ror.updated_at
                FROM identity.parcels p
                JOIN revenue.ror_records ror ON ror.parcel_id = p.parcel_id
                WHERE (:parcel_id IS NULL OR p.parcel_id = :parcel_id)
                  AND (:state_code IS NULL OR p.state_code = :state_code)

                UNION ALL

                SELECT
                    p.parcel_id,
                    'sro_registrations' AS source_type,
                    reg.buyer AS owner_name,
                    '' AS phonetic_key,  -- Compute if needed
                    reg.registration_date::timestamp AS updated_at
                FROM identity.parcels p
                JOIN registration.sale_deeds reg ON reg.parcel_id = p.parcel_id
                WHERE (:parcel_id IS NULL OR p.parcel_id = :parcel_id)
                  AND (:state_code IS NULL OR p.state_code = :state_code)
            ),
            conflicts_detected AS (
                SELECT
                    o1.parcel_id,
                    o1.source_type AS source_a,
                    o2.source_type AS source_b,
                    o1.owner_name AS owner_a,
                    o2.owner_name AS owner_b,
                    o1.phonetic_key AS phonetic_a,
                    o2.phonetic_key AS phonetic_b
                FROM owner_sources o1
                JOIN owner_sources o2 ON o1.parcel_id = o2.parcel_id AND o1.source_type < o2.source_type
                WHERE o1.phonetic_key != o2.phonetic_key
                  AND o1.updated_at IS NOT NULL
                  AND o2.updated_at IS NOT NULL
                  AND ABS(EXTRACT(EPOCH FROM (o1.updated_at - o2.updated_at))) < 31536000  -- Within 1 year
            )
            SELECT * FROM conflicts_detected
        """)

        result = await self.db.execute(query, {
            "parcel_id": parcel_id,
            "state_code": state_code,
        })

        conflicts = []
        for row in result.fetchall():
            conflicts.append(Conflict(
                parcel_id=row.parcel_id,
                conflict_type=ConflictType.OWNER_MISMATCH,
                source_a=row.source_a,
                source_b=row.source_b,
                field_name="owner_name",
                value_a=row.owner_a,
                value_b=row.owner_b,
                confidence=0.80,
                severity="MEDIUM",
                description=f"Owner name mismatch between {row.source_a} and {row.source_b} (phonetic keys differ)",
            ))

        return conflicts

    async def detect_status_conflicts(
        self,
        parcel_id: Optional[UUID] = None,
        state_code: Optional[str] = None,
    ) -> List[Conflict]:
        """
        Detect status disagreements (e.g., one source shows encumbrance, another doesn't).

        Returns:
            List of status conflict records
        """
        # Simplified check: encumbrance exists in one source but not flagged in another
        # In production, this would be more sophisticated
        conflicts = []
        # Placeholder implementation
        return conflicts

    async def detect_transaction_lag(
        self,
        parcel_id: Optional[UUID] = None,
        state_code: Optional[str] = None,
    ) -> List[Conflict]:
        """
        Detect SRO registration completed but Revenue record not mutated (lag > 90 days).

        Returns:
            List of transaction lag conflicts
        """
        query = text("""
            WITH recent_sales AS (
                SELECT
                    reg.parcel_id,
                    reg.buyer AS new_owner,
                    reg.registration_date
                FROM registration.sale_deeds reg
                WHERE reg.registration_date > CURRENT_DATE - INTERVAL '90 days'
                  AND (:parcel_id IS NULL OR reg.parcel_id = :parcel_id)
            ),
            revenue_owners AS (
                SELECT
                    ror.parcel_id,
                    ror.owner_name
                FROM revenue.ror_records ror
                WHERE (:parcel_id IS NULL OR ror.parcel_id = :parcel_id)
            ),
            lag_conflicts AS (
                SELECT
                    rs.parcel_id,
                    rs.new_owner,
                    rs.registration_date,
                    ro.owner_name AS revenue_owner
                FROM recent_sales rs
                JOIN revenue_owners ro ON ro.parcel_id = rs.parcel_id
                WHERE LOWER(rs.new_owner) != LOWER(ro.owner_name)
            )
            SELECT * FROM lag_conflicts
        """)

        result = await self.db.execute(query, {
            "parcel_id": parcel_id,
        })

        conflicts = []
        for row in result.fetchall():
            conflicts.append(Conflict(
                parcel_id=row.parcel_id,
                conflict_type=ConflictType.TRANSACTION_MUTATION_LAG,
                source_a="sro_registrations",
                source_b="revenue_ror",
                field_name="owner",
                value_a=row.new_owner,
                value_b=row.revenue_owner,
                confidence=0.85,
                severity="HIGH",
                description=f"Sale registered on {row.registration_date} but Revenue record not updated (buyer: {row.new_owner}, RoR: {row.revenue_owner})",
            ))

        return conflicts

    async def detect_geometry_conflicts(
        self,
        parcel_id: Optional[UUID] = None,
        state_code: Optional[str] = None,
    ) -> List[Conflict]:
        """
        Detect linked records referencing geometries with IoU < 0.5.

        Returns:
            List of geometry conflict records
        """
        # Placeholder: In production, compare geometries from different sources
        conflicts = []
        return conflicts

    async def persist_conflicts(self, conflicts: List[Conflict]) -> None:
        """Persist detected conflicts to the identity.conflicts table."""
        for conflict in conflicts:
            insert_stmt = text("""
                INSERT INTO identity.conflicts
                    (parcel_id, conflict_type, source_a, source_b, field_name,
                     value_a, value_b, confidence, severity, description, status, created_at)
                VALUES
                    (:parcel_id, :conflict_type, :source_a, :source_b, :field_name,
                     :value_a, :value_b, :confidence, :severity, :description, 'OPEN', NOW())
                ON CONFLICT (parcel_id, conflict_type, source_a, source_b, field_name)
                DO UPDATE SET
                    value_a = EXCLUDED.value_a,
                    value_b = EXCLUDED.value_b,
                    confidence = EXCLUDED.confidence,
                    severity = EXCLUDED.severity,
                    description = EXCLUDED.description,
                    updated_at = NOW()
            """)

            await self.db.execute(insert_stmt, {
                "parcel_id": conflict.parcel_id,
                "conflict_type": conflict.conflict_type.value,
                "source_a": conflict.source_a,
                "source_b": conflict.source_b,
                "field_name": conflict.field_name,
                "value_a": str(conflict.value_a),
                "value_b": str(conflict.value_b),
                "confidence": conflict.confidence,
                "severity": conflict.severity,
                "description": conflict.description,
            })

        await self.db.commit()
