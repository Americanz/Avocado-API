"""
Payment models for sales management.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLAlchemyEnum,
    Float,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import relationship

from src.core.models.base_model import BaseModel


class PaymentMethod(str, Enum):
    """Payment method enum."""

    CASH = "cash"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    ONLINE = "online"
    CREDIT = "credit"
    OTHER = "other"


class PaymentType(str, Enum):
    """Payment type enum."""

    PAYMENT = "payment"
    REFUND = "refund"
    PREPAYMENT = "prepayment"


class Payment(BaseModel):
    """Payment model for financial transactions."""

    __tablename__ = "payments"

    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    method = Column(
        SQLAlchemyEnum(PaymentMethod), nullable=False, default=PaymentMethod.CASH
    )
    payment_type = Column(
        SQLAlchemyEnum(PaymentType), nullable=False, default=PaymentType.PAYMENT
    )
    reference = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    # Foreign keys
    order_id = Column(PgUUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    client_id = Column(PgUUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)

    

    def __repr__(self) -> str:
        return f"<Payment {self.amount} via {self.method}>"
