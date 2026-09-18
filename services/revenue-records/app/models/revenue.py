import uuid
from sqlalchemy import (
    Column, String, Numeric, Date, DateTime, Integer,
    ForeignKey, Text, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base


class RecordOfRights(Base):
    __tablename__ = "records_of_rights"
    __table_args__ = {"schema": "revenue"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parcel_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    ror_id = Column(String, nullable=True)
    record_date = Column(Date, nullable=True)
    survey_number = Column(String, nullable=True)
    land_classification = Column(String, nullable=True)
    land_use = Column(String, nullable=True)
    area_sq_m = Column(Numeric, nullable=True)
    area_native = Column(Numeric, nullable=True)
    area_unit_native = Column(String, nullable=True)
    source_department = Column(String, nullable=True)
    source_as_of_date = Column(Date, nullable=True)
    data_freshness_status = Column(String, nullable=False, server_default="DEMO")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    rights = relationship("Right", back_populates="record_of_rights", lazy="selectin")


class Party(Base):
    __tablename__ = "parties"
    __table_args__ = {"schema": "revenue"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    party_type = Column(String, nullable=False)
    name_en = Column(String, nullable=False)
    name_local = Column(String, nullable=True)
    name_phonetic_key = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    rights = relationship("Right", back_populates="party", lazy="noload")
    mutations_from = relationship(
        "Mutation", foreign_keys="Mutation.from_party_id", back_populates="from_party", lazy="noload"
    )
    mutations_to = relationship(
        "Mutation", foreign_keys="Mutation.to_party_id", back_populates="to_party", lazy="noload"
    )


class Right(Base):
    __tablename__ = "rights"
    __table_args__ = {"schema": "revenue"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parcel_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    ror_id = Column(UUID(as_uuid=True), ForeignKey("revenue.records_of_rights.id"), nullable=True)
    right_type = Column(String, nullable=False)
    party_id = Column(UUID(as_uuid=True), ForeignKey("revenue.parties.id"), nullable=True)
    share_numerator = Column(Integer, nullable=True)
    share_denominator = Column(Integer, nullable=True)
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    record_of_rights = relationship("RecordOfRights", back_populates="rights", lazy="noload")
    party = relationship("Party", back_populates="rights", lazy="selectin")


class Mutation(Base):
    __tablename__ = "mutations"
    __table_args__ = {"schema": "revenue"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parcel_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    mutation_type = Column(String, nullable=False)
    from_party_id = Column(UUID(as_uuid=True), ForeignKey("revenue.parties.id"), nullable=True)
    to_party_id = Column(UUID(as_uuid=True), ForeignKey("revenue.parties.id"), nullable=True)
    status = Column(String, nullable=False, server_default="PENDING")
    officer_id = Column(String, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(String, nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    from_party = relationship("Party", foreign_keys=[from_party_id], back_populates="mutations_from", lazy="noload")
    to_party = relationship("Party", foreign_keys=[to_party_id], back_populates="mutations_to", lazy="noload")
