"""
ORM models for the geo PostgreSQL schema.

Geometry columns (PostGIS MULTIPOLYGON/GEOMETRY) are declared as Text
placeholders in the ORM models.  All actual spatial operations — tile
generation, area queries, intersections — use raw SQL via sqlalchemy.text()
so that we can leverage PostGIS functions without adding a geoalchemy2
dependency.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# geo.parcel_geometries
# ---------------------------------------------------------------------------

class ParcelGeometry(Base):
    """
    Stores the official geometry for each active version of a parcel.

    Multiple version rows may exist per parcel_id (historical geometries);
    only the row with is_active=True is the current boundary.
    """
    __tablename__ = "parcel_geometries"
    __table_args__ = {"schema": "geo"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    parcel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    # geometry GEOMETRY(MULTIPOLYGON, 4326) — handled exclusively via raw SQL
    accuracy_class: Mapped[str | None] = mapped_column(String(20), nullable=True)
    crs_native: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_survey_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    area_sq_m: Mapped[float | None] = mapped_column(Numeric(20, 4), nullable=True)
    area_native: Mapped[float | None] = mapped_column(Numeric(20, 6), nullable=True)
    area_unit_native: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


# ---------------------------------------------------------------------------
# geo.administrative_boundaries
# ---------------------------------------------------------------------------

class AdministrativeBoundary(Base):
    """LGD administrative hierarchy polygons (state/district/subdistrict/village)."""
    __tablename__ = "administrative_boundaries"
    __table_args__ = {"schema": "geo"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # STATE | DISTRICT | SUBDISTRICT | VILLAGE | URBAN_WARD
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    lgd_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    name_en: Mapped[str | None] = mapped_column(String(200), nullable=True)
    name_local: Mapped[str | None] = mapped_column(String(200), nullable=True)
    parent_lgd_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # geometry GEOMETRY(MULTIPOLYGON, 4326) — handled via raw SQL
    # RURAL | URBAN
    hierarchy_type: Mapped[str | None] = mapped_column(String(20), nullable=True)


# ---------------------------------------------------------------------------
# geo.restriction_zones
# ---------------------------------------------------------------------------

class RestrictionZone(Base):
    """
    Protected areas, buffer zones, and regulatory exclusion areas
    that constrain what can be done with parcels that intersect them.
    """
    __tablename__ = "restriction_zones"
    __table_args__ = {"schema": "geo"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    zone_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    # geometry GEOMETRY(GEOMETRY, 4326) — handled via raw SQL
    legal_basis: Mapped[str | None] = mapped_column(String(200), nullable=True)
    buffer_metres: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )


# ---------------------------------------------------------------------------
# geo.topology_conflicts
# ---------------------------------------------------------------------------

class TopologyConflict(Base):
    """
    Detected topology errors: overlapping parcels, slivers, gaps.
    Created by the conflict-detection engine; resolved by a revenue officer.
    """
    __tablename__ = "topology_conflicts"
    __table_args__ = {"schema": "geo"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # OVERLAP | GAP | SLIVER | SELF_INTERSECTION
    conflict_type: Mapped[str] = mapped_column(String(50), nullable=False)
    parcel_id_1: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    parcel_id_2: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    # geometry GEOMETRY(GEOMETRY, 4326) — handled via raw SQL (conflict intersection)
    overlap_area_sq_m: Mapped[float | None] = mapped_column(
        Numeric(20, 4), nullable=True
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # OPEN | RESOLVED | DISMISSED
    resolution_status: Mapped[str] = mapped_column(
        String(20), default="OPEN", nullable=False
    )
