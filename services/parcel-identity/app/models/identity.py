"""
ORM models for the identity PostgreSQL schema.

Tables live in the `identity` schema — every model sets
__table_args__ = {"schema": "identity"} accordingly.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# identity.parcels
# ---------------------------------------------------------------------------

class Parcel(Base):
    """
    Canonical parcel identity record.

    Every land parcel anywhere in India gets exactly one row here.
    The BDPR is the platform's own stable identifier; ULPIN is the
    national identifier once it has been assigned and verified.
    """
    __tablename__ = "parcels"
    __table_args__ = {"schema": "identity"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    bdpr: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    ulpin: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    ulpin_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ulpin_assigned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    state_code: Mapped[str] = mapped_column(String(10), nullable=False)
    district_code: Mapped[str] = mapped_column(String(10), nullable=False)
    subdistrict_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    village_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    urban_ward_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_urban: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # AUTHORITATIVE | DERIVED | CACHE
    system_of_record_flag: Mapped[str] = mapped_column(
        String(20), default="DERIVED", nullable=False
    )

    # Relationships
    lineage_as_parent: Mapped[list[ParcelLineage]] = relationship(
        "ParcelLineage",
        foreign_keys="ParcelLineage.parent_parcel_id",
        back_populates="parent_parcel",
        lazy="select",
    )
    lineage_as_child: Mapped[list[ParcelLineage]] = relationship(
        "ParcelLineage",
        foreign_keys="ParcelLineage.child_parcel_id",
        back_populates="child_parcel",
        lazy="select",
    )
    aliases: Mapped[list[ParcelAlias]] = relationship(
        "ParcelAlias", back_populates="parcel", lazy="select"
    )


# ---------------------------------------------------------------------------
# identity.parcel_lineage
# ---------------------------------------------------------------------------

class ParcelLineage(Base):
    """
    Records subdivision, amalgamation, boundary correction, and
    resurvey/renumber events between parent and child parcels.
    """
    __tablename__ = "parcel_lineage"
    __table_args__ = {"schema": "identity"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # SUBDIVISION | AMALGAMATION | BOUNDARY_CORRECTION | RESURVEY_RENUMBER
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    parent_parcel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity.parcels.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    child_parcel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity.parcels.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    authorising_document: Mapped[str | None] = mapped_column(String(200), nullable=True)
    authorising_authority: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    parent_parcel: Mapped[Parcel | None] = relationship(
        "Parcel",
        foreign_keys=[parent_parcel_id],
        back_populates="lineage_as_parent",
    )
    child_parcel: Mapped[Parcel | None] = relationship(
        "Parcel",
        foreign_keys=[child_parcel_id],
        back_populates="lineage_as_child",
    )


# ---------------------------------------------------------------------------
# identity.parcel_aliases
# ---------------------------------------------------------------------------

class ParcelAlias(Base):
    """
    Maps external identifiers (survey numbers, khasra numbers, account
    numbers, etc.) to the canonical BDPR-based parcel record.
    """
    __tablename__ = "parcel_aliases"
    __table_args__ = {"schema": "identity"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    parcel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity.parcels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # e.g. SURVEY_NUMBER, KHASRA, ACCOUNT_NO, PATTA_NO
    alias_type: Mapped[str] = mapped_column(String(50), nullable=False)
    alias_value: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    source_system: Mapped[str | None] = mapped_column(String(100), nullable=True)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)

    parcel: Mapped[Parcel] = relationship("Parcel", back_populates="aliases")
