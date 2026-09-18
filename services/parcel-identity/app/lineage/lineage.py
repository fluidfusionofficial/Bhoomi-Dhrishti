"""
Parcel lineage graph management: subdivision, amalgamation, boundary corrections, resurvey.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class LineageManager:
    """Manages parcel lifecycle events and lineage chains."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def record_subdivision(
        self,
        parent_ulpin: str,
        child_ulpins: List[str],
        event_date: date,
        authorising_doc: str,
    ) -> int:
        """
        Record a subdivision event: one parcel → multiple child parcels.

        Args:
            parent_ulpin: ULPIN of parent parcel
            child_ulpins: List of child parcel ULPINs
            event_date: Date of subdivision
            authorising_doc: Survey/legal document number

        Returns:
            Event ID
        """
        # Get parent parcel_id
        parent_query = text("SELECT parcel_id FROM identity.parcels WHERE ulpin = :ulpin")
        parent_result = await self.db.execute(parent_query, {"ulpin": parent_ulpin})
        parent_row = parent_result.fetchone()

        if not parent_row:
            raise ValueError(f"Parent parcel with ULPIN {parent_ulpin} not found")

        parent_id = parent_row.parcel_id

        # Get child parcel_ids
        child_ids = []
        for child_ulpin in child_ulpins:
            child_query = text("SELECT parcel_id FROM identity.parcels WHERE ulpin = :ulpin")
            child_result = await self.db.execute(child_query, {"ulpin": child_ulpin})
            child_row = child_result.fetchone()
            if child_row:
                child_ids.append(child_row.parcel_id)

        # Insert event
        insert_stmt = text("""
            INSERT INTO identity.parcel_events
                (event_type, parent_parcel_ids, child_parcel_ids, event_date,
                 authorising_document, metadata, created_at)
            VALUES
                ('SUBDIVISION', ARRAY[:parent_id]::uuid[], :child_ids::uuid[],
                 :event_date, :doc, '{}'::jsonb, NOW())
            RETURNING event_id
        """)

        result = await self.db.execute(insert_stmt, {
            "parent_id": parent_id,
            "child_ids": child_ids,
            "event_date": event_date,
            "doc": authorising_doc,
        })
        event_id = result.scalar()
        await self.db.commit()

        return event_id

    async def record_amalgamation(
        self,
        parent_ulpins: List[str],
        child_ulpin: str,
        event_date: date,
        authorising_doc: str,
    ) -> int:
        """
        Record an amalgamation event: multiple parcels → one merged parcel.

        Args:
            parent_ulpins: List of parent parcel ULPINs being merged
            child_ulpin: ULPIN of merged result parcel
            event_date: Date of amalgamation
            authorising_doc: Survey/legal document number

        Returns:
            Event ID
        """
        # Get parent parcel_ids
        parent_ids = []
        for ulpin in parent_ulpins:
            query = text("SELECT parcel_id FROM identity.parcels WHERE ulpin = :ulpin")
            result = await self.db.execute(query, {"ulpin": ulpin})
            row = result.fetchone()
            if row:
                parent_ids.append(row.parcel_id)

        # Get child parcel_id
        child_query = text("SELECT parcel_id FROM identity.parcels WHERE ulpin = :ulpin")
        child_result = await self.db.execute(child_query, {"ulpin": child_ulpin})
        child_row = child_result.fetchone()

        if not child_row:
            raise ValueError(f"Child parcel with ULPIN {child_ulpin} not found")

        child_id = child_row.parcel_id

        # Insert event
        insert_stmt = text("""
            INSERT INTO identity.parcel_events
                (event_type, parent_parcel_ids, child_parcel_ids, event_date,
                 authorising_document, metadata, created_at)
            VALUES
                ('AMALGAMATION', :parent_ids::uuid[], ARRAY[:child_id]::uuid[],
                 :event_date, :doc, '{}'::jsonb, NOW())
            RETURNING event_id
        """)

        result = await self.db.execute(insert_stmt, {
            "parent_ids": parent_ids,
            "child_id": child_id,
            "event_date": event_date,
            "doc": authorising_doc,
        })
        event_id = result.scalar()
        await self.db.commit()

        return event_id

    async def record_boundary_correction(
        self,
        parcel_id: UUID,
        old_geom_wkt: str,
        new_geom_wkt: str,
        event_date: date,
        authorising_doc: str = "",
    ) -> int:
        """
        Record a boundary correction (geometry change without parcel split/merge).

        Args:
            parcel_id: Parcel whose boundary was corrected
            old_geom_wkt: Old geometry as WKT
            new_geom_wkt: New geometry as WKT
            event_date: Date of correction
            authorising_doc: Survey/correction document

        Returns:
            Event ID
        """
        metadata = {
            "old_geometry_wkt": old_geom_wkt[:500],  # Truncate for storage
            "new_geometry_wkt": new_geom_wkt[:500],
        }

        insert_stmt = text("""
            INSERT INTO identity.parcel_events
                (event_type, parent_parcel_ids, child_parcel_ids, event_date,
                 authorising_document, metadata, created_at)
            VALUES
                ('BOUNDARY_CORRECTION', ARRAY[:parcel_id]::uuid[], ARRAY[:parcel_id]::uuid[],
                 :event_date, :doc, :metadata::jsonb, NOW())
            RETURNING event_id
        """)

        result = await self.db.execute(insert_stmt, {
            "parcel_id": parcel_id,
            "event_date": event_date,
            "doc": authorising_doc,
            "metadata": metadata,
        })
        event_id = result.scalar()
        await self.db.commit()

        return event_id

    async def record_resurvey_renumber(
        self,
        old_survey: str,
        new_survey: str,
        parcel_id: UUID,
        event_date: date,
        authorising_doc: str = "",
    ) -> int:
        """
        Record a survey number renumbering event (post-resurvey).

        Args:
            old_survey: Old survey number
            new_survey: New survey number
            parcel_id: Parcel that was renumbered
            event_date: Date of resurvey
            authorising_doc: Survey document

        Returns:
            Event ID
        """
        metadata = {
            "old_survey_number": old_survey,
            "new_survey_number": new_survey,
        }

        insert_stmt = text("""
            INSERT INTO identity.parcel_events
                (event_type, parent_parcel_ids, child_parcel_ids, event_date,
                 authorising_document, metadata, created_at)
            VALUES
                ('RESURVEY_RENUMBER', ARRAY[:parcel_id]::uuid[], ARRAY[:parcel_id]::uuid[],
                 :event_date, :doc, :metadata::jsonb, NOW())
            RETURNING event_id
        """)

        result = await self.db.execute(insert_stmt, {
            "parcel_id": parcel_id,
            "event_date": event_date,
            "doc": authorising_doc,
            "metadata": metadata,
        })
        event_id = result.scalar()
        await self.db.commit()

        # Also register old survey number as an alias
        alias_stmt = text("""
            INSERT INTO identity.parcel_aliases
                (parcel_id, alias_type, alias_value, source_system, created_at)
            VALUES
                (:parcel_id, 'OLD_SURVEY_NUMBER', :old_survey, 'RESURVEY', NOW())
            ON CONFLICT DO NOTHING
        """)
        await self.db.execute(alias_stmt, {
            "parcel_id": parcel_id,
            "old_survey": old_survey,
        })
        await self.db.commit()

        return event_id

    async def get_lineage_chain(self, parcel_id: UUID) -> Dict[str, Any]:
        """
        Get full lineage chain (ancestry and descendants) for a parcel.

        Returns:
            Dict with 'ancestors', 'descendants', 'events' as adjacency lists
        """
        # Recursive query to get ancestors
        ancestors_query = text("""
            WITH RECURSIVE lineage AS (
                SELECT
                    event_id,
                    event_type,
                    parent_parcel_ids,
                    child_parcel_ids,
                    event_date,
                    1 AS depth
                FROM identity.parcel_events
                WHERE :parcel_id = ANY(child_parcel_ids)

                UNION ALL

                SELECT
                    pe.event_id,
                    pe.event_type,
                    pe.parent_parcel_ids,
                    pe.child_parcel_ids,
                    pe.event_date,
                    l.depth + 1
                FROM identity.parcel_events pe
                JOIN lineage l ON pe.child_parcel_ids && l.parent_parcel_ids
                WHERE l.depth < 10
            )
            SELECT
                event_id,
                event_type,
                parent_parcel_ids,
                child_parcel_ids,
                event_date
            FROM lineage
            ORDER BY depth ASC
        """)

        ancestors_result = await self.db.execute(ancestors_query, {"parcel_id": parcel_id})
        ancestors = [dict(row._mapping) for row in ancestors_result.fetchall()]

        # Recursive query to get descendants
        descendants_query = text("""
            WITH RECURSIVE lineage AS (
                SELECT
                    event_id,
                    event_type,
                    parent_parcel_ids,
                    child_parcel_ids,
                    event_date,
                    1 AS depth
                FROM identity.parcel_events
                WHERE :parcel_id = ANY(parent_parcel_ids)

                UNION ALL

                SELECT
                    pe.event_id,
                    pe.event_type,
                    pe.parent_parcel_ids,
                    pe.child_parcel_ids,
                    pe.event_date,
                    l.depth + 1
                FROM identity.parcel_events pe
                JOIN lineage l ON pe.parent_parcel_ids && l.child_parcel_ids
                WHERE l.depth < 10
            )
            SELECT
                event_id,
                event_type,
                parent_parcel_ids,
                child_parcel_ids,
                event_date
            FROM lineage
            ORDER BY depth ASC
        """)

        descendants_result = await self.db.execute(descendants_query, {"parcel_id": parcel_id})
        descendants = [dict(row._mapping) for row in descendants_result.fetchall()]

        return {
            "parcel_id": str(parcel_id),
            "ancestors": ancestors,
            "descendants": descendants,
        }
