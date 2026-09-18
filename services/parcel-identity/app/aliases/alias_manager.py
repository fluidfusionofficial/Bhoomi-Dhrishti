"""
Legacy identifier alias management for parcels.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class AliasType(str, Enum):
    """Types of parcel identifier aliases."""
    ULPIN = "ULPIN"
    SURVEY_NUMBER = "SURVEY_NUMBER"
    MUNICIPAL_PID = "MUNICIPAL_PID"
    TAX_ASSESSMENT = "TAX_ASSESSMENT"
    OLD_SURVEY_NUMBER = "OLD_SURVEY_NUMBER"
    REGISTRATION_DOC_NUMBER = "REGISTRATION_DOC_NUMBER"


class AliasManager:
    """Manages alternative identifiers for parcels."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def register_alias(
        self,
        parcel_id: UUID,
        alias_type: AliasType,
        alias_value: str,
        source_system: str,
    ) -> int:
        """
        Register an alternative identifier for a parcel.

        Args:
            parcel_id: Canonical parcel ID
            alias_type: Type of alias (survey number, tax ID, etc.)
            alias_value: The alias value
            source_system: System that uses this identifier

        Returns:
            Alias ID
        """
        insert_stmt = text("""
            INSERT INTO identity.parcel_aliases
                (parcel_id, alias_type, alias_value, source_system, created_at)
            VALUES
                (:parcel_id, :alias_type, :alias_value, :source_system, NOW())
            ON CONFLICT (parcel_id, alias_type, alias_value)
            DO UPDATE SET
                source_system = EXCLUDED.source_system,
                updated_at = NOW()
            RETURNING alias_id
        """)

        result = await self.db.execute(insert_stmt, {
            "parcel_id": parcel_id,
            "alias_type": alias_type.value,
            "alias_value": alias_value,
            "source_system": source_system,
        })
        alias_id = result.scalar()
        await self.db.commit()

        return alias_id

    async def resolve_alias(
        self,
        alias_type: AliasType,
        alias_value: str,
    ) -> Optional[UUID]:
        """
        Resolve an alias to a canonical parcel ID.

        Args:
            alias_type: Type of alias
            alias_value: The alias value to resolve

        Returns:
            Canonical parcel_id if found, else None
        """
        query = text("""
            SELECT parcel_id
            FROM identity.parcel_aliases
            WHERE alias_type = :alias_type
              AND alias_value = :alias_value
            LIMIT 1
        """)

        result = await self.db.execute(query, {
            "alias_type": alias_type.value,
            "alias_value": alias_value,
        })
        row = result.fetchone()

        return row.parcel_id if row else None

    async def get_all_aliases(self, parcel_id: UUID) -> list[dict]:
        """
        Get all registered aliases for a parcel.

        Args:
            parcel_id: Canonical parcel ID

        Returns:
            List of alias records
        """
        query = text("""
            SELECT
                alias_id,
                alias_type,
                alias_value,
                source_system,
                created_at
            FROM identity.parcel_aliases
            WHERE parcel_id = :parcel_id
            ORDER BY created_at DESC
        """)

        result = await self.db.execute(query, {"parcel_id": parcel_id})
        return [dict(row._mapping) for row in result.fetchall()]
