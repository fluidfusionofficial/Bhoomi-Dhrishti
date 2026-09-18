"""SQLAlchemy bulk data loader with conflict resolution."""

from typing import Any, Dict, List, Optional

import structlog
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class LoadError(Exception):
    """Raised when data loading fails."""

    pass


class DataLoader:
    """Async bulk data loader with upsert support."""

    def __init__(self, session: AsyncSession):
        """
        Initialize loader with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def load_parcels(
        self,
        records: List[Dict[str, Any]],
        conflict_strategy: str = "update"
    ) -> int:
        """
        Load parcel records to identity.parcels table.

        Args:
            records: List of parcel records
            conflict_strategy: "update" (upsert) or "ignore" (skip conflicts)

        Returns:
            Number of rows inserted/updated
        """
        if not records:
            return 0

        try:
            # Build INSERT statement with ON CONFLICT
            stmt = """
                INSERT INTO identity.parcels (
                    survey_number,
                    district_code,
                    village_code,
                    area_sq_m,
                    geometry_wkt,
                    created_at,
                    updated_at
                )
                VALUES (
                    :survey_number,
                    :district_code,
                    :village_code,
                    :area_sq_m,
                    :geometry_wkt,
                    NOW(),
                    NOW()
                )
                ON CONFLICT (survey_number, district_code, village_code)
            """

            if conflict_strategy == "update":
                stmt += """
                    DO UPDATE SET
                        area_sq_m = EXCLUDED.area_sq_m,
                        geometry_wkt = EXCLUDED.geometry_wkt,
                        updated_at = NOW()
                """
            else:  # ignore
                stmt += " DO NOTHING"

            # Execute in batches
            batch_size = 1000
            total_processed = 0

            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                result = await self.session.execute(text(stmt), batch)
                total_processed += result.rowcount

            await self.session.commit()

            logger.info(
                "parcels_loaded",
                total_records=len(records),
                rows_affected=total_processed,
                conflict_strategy=conflict_strategy
            )

            return total_processed

        except Exception as e:
            await self.session.rollback()
            logger.error("parcel_load_error", error=str(e))
            raise LoadError(f"Failed to load parcels: {e}")

    async def load_ror_records(
        self,
        records: List[Dict[str, Any]],
        conflict_strategy: str = "update"
    ) -> int:
        """
        Load RoR records to revenue.ror_records table.

        Args:
            records: List of RoR records
            conflict_strategy: "update" (upsert) or "ignore" (skip conflicts)

        Returns:
            Number of rows inserted/updated
        """
        if not records:
            return 0

        try:
            stmt = """
                INSERT INTO revenue.ror_records (
                    survey_number,
                    district_code,
                    village_code,
                    area_native,
                    area_sq_m,
                    unit_native,
                    owner_name,
                    owner_name_local,
                    owner_name_phonetic,
                    land_use,
                    registration_date,
                    created_at,
                    updated_at
                )
                VALUES (
                    :survey_number,
                    :district_code,
                    :village_code,
                    :area_native,
                    :area_sq_m,
                    :unit_native,
                    :owner_name,
                    :owner_name_local,
                    :owner_name_phonetic,
                    :land_use,
                    :registration_date,
                    NOW(),
                    NOW()
                )
                ON CONFLICT (survey_number, district_code, village_code)
            """

            if conflict_strategy == "update":
                stmt += """
                    DO UPDATE SET
                        area_native = EXCLUDED.area_native,
                        area_sq_m = EXCLUDED.area_sq_m,
                        unit_native = EXCLUDED.unit_native,
                        owner_name = EXCLUDED.owner_name,
                        owner_name_local = EXCLUDED.owner_name_local,
                        owner_name_phonetic = EXCLUDED.owner_name_phonetic,
                        land_use = EXCLUDED.land_use,
                        registration_date = EXCLUDED.registration_date,
                        updated_at = NOW()
                """
            else:  # ignore
                stmt += " DO NOTHING"

            # Execute in batches
            batch_size = 1000
            total_processed = 0

            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                result = await self.session.execute(text(stmt), batch)
                total_processed += result.rowcount

            await self.session.commit()

            logger.info(
                "ror_records_loaded",
                total_records=len(records),
                rows_affected=total_processed,
                conflict_strategy=conflict_strategy
            )

            return total_processed

        except Exception as e:
            await self.session.rollback()
            logger.error("ror_load_error", error=str(e))
            raise LoadError(f"Failed to load RoR records: {e}")

    async def load_registrations(
        self,
        records: List[Dict[str, Any]],
        conflict_strategy: str = "update"
    ) -> int:
        """
        Load sale deed registrations to registration.sale_deeds table.

        Args:
            records: List of registration records
            conflict_strategy: "update" (upsert) or "ignore" (skip conflicts)

        Returns:
            Number of rows inserted/updated
        """
        if not records:
            return 0

        try:
            stmt = """
                INSERT INTO registration.sale_deeds (
                    registration_number,
                    registration_date,
                    survey_number,
                    district_code,
                    village_code,
                    sro_code,
                    area_sq_m,
                    consideration_amount,
                    seller_name,
                    buyer_name,
                    document_type,
                    created_at,
                    updated_at
                )
                VALUES (
                    :registration_number,
                    :registration_date,
                    :survey_number,
                    :district_code,
                    :village_code,
                    :sro_code,
                    :area_sq_m,
                    :consideration_amount,
                    :seller_name,
                    :buyer_name,
                    :document_type,
                    NOW(),
                    NOW()
                )
                ON CONFLICT (registration_number, district_code)
            """

            if conflict_strategy == "update":
                stmt += """
                    DO UPDATE SET
                        registration_date = EXCLUDED.registration_date,
                        survey_number = EXCLUDED.survey_number,
                        village_code = EXCLUDED.village_code,
                        sro_code = EXCLUDED.sro_code,
                        area_sq_m = EXCLUDED.area_sq_m,
                        consideration_amount = EXCLUDED.consideration_amount,
                        seller_name = EXCLUDED.seller_name,
                        buyer_name = EXCLUDED.buyer_name,
                        document_type = EXCLUDED.document_type,
                        updated_at = NOW()
                """
            else:  # ignore
                stmt += " DO NOTHING"

            # Execute in batches
            batch_size = 1000
            total_processed = 0

            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                result = await self.session.execute(text(stmt), batch)
                total_processed += result.rowcount

            await self.session.commit()

            logger.info(
                "registrations_loaded",
                total_records=len(records),
                rows_affected=total_processed,
                conflict_strategy=conflict_strategy
            )

            return total_processed

        except Exception as e:
            await self.session.rollback()
            logger.error("registration_load_error", error=str(e))
            raise LoadError(f"Failed to load registrations: {e}")

    async def execute_custom_load(
        self,
        table_name: str,
        records: List[Dict[str, Any]],
        conflict_columns: Optional[List[str]] = None,
        conflict_strategy: str = "update"
    ) -> int:
        """
        Generic loader for custom table targets.

        Args:
            table_name: Fully qualified table name (schema.table)
            records: List of records to load
            conflict_columns: Columns for conflict detection
            conflict_strategy: "update" or "ignore"

        Returns:
            Number of rows affected
        """
        if not records:
            return 0

        try:
            # This is a simplified version. In production, build dynamic SQL
            # based on record keys and conflict columns
            logger.info(
                "custom_load_started",
                table=table_name,
                record_count=len(records),
                conflict_columns=conflict_columns
            )

            # For now, just insert without conflict handling
            # In production, dynamically build INSERT...ON CONFLICT statement
            raise NotImplementedError("Custom loader requires dynamic SQL generation")

        except Exception as e:
            await self.session.rollback()
            logger.error("custom_load_error", table=table_name, error=str(e))
            raise LoadError(f"Failed to load to {table_name}: {e}")
