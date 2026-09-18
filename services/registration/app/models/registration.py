import uuid
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID

from app.db import Base


class Deed(Base):
    __tablename__ = "deeds"
    __table_args__ = {"schema": "registration"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parcel_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    deed_number = Column(String(100), nullable=True)
    deed_type = Column(String(100), nullable=True)
    sro_code = Column(String(50), nullable=True)
    registration_date = Column(Date, nullable=True)
    consideration_amount = Column(Numeric(20, 2), nullable=True)
    seller_party_id = Column(UUID(as_uuid=True), nullable=True)
    buyer_party_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Encumbrance(Base):
    __tablename__ = "encumbrances"
    __table_args__ = {"schema": "registration"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parcel_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    encumbrance_type = Column(String(100), nullable=False)
    in_favour_of_party_id = Column(UUID(as_uuid=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    amount = Column(Numeric(20, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)


class Party(Base):
    """Reference model for revenue.parties — read-only joins."""

    __tablename__ = "parties"
    __table_args__ = {"schema": "revenue"}

    id = Column(UUID(as_uuid=True), primary_key=True)
    party_type = Column(String(50), nullable=True)
    name_en = Column(String(255), nullable=True)
    name_local = Column(String(255), nullable=True)


class TransactionNetworkFlag(Base):
    """Reference model for ml.transaction_network_flags."""

    __tablename__ = "transaction_network_flags"
    __table_args__ = {"schema": "ml"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parcel_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    flag_type = Column(String(100), nullable=True)
    confidence_score = Column(Numeric(5, 4), nullable=True)
    flagged_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # JSONB stored as Text for portability; parse with json.loads if needed
    details = Column(Text, nullable=True)
    is_resolved = Column(Boolean, default=False, nullable=False)
