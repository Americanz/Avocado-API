"""
Transaction bonus model
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    BigInteger,
    ForeignKey,
    Numeric,
    Text,
    DateTime,
)
from sqlalchemy.orm import relationship
from src.core.models.base_model import BaseModel


class TransactionBonus(BaseModel):
    """
    Bonus operations history for clients
    Tracks all bonus earning and spending operations
    """

    __tablename__ = "transaction_bonus"

    use_generic_routes = True
    search_fields = ["client_id", "operation_type", "description"]
    default_order_by = ["-created_at"]

    # Link to client
    client_id = Column(
        BigInteger,
        ForeignKey("clients.client_id"),
        nullable=False,
        index=True,
        comment="Client ID from Poster",
    )

    # Link to poster transaction (if applicable)
    transaction_id = Column(
        BigInteger,
        ForeignKey("transactions.transaction_id"),
        nullable=True,
        index=True,
        comment="Related Poster transaction ID",
    )

    # Operation details
    operation_type = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Operation type: EARN, SPEND, ADJUST, EXPIRE",
    )

    # Amounts
    amount = Column(
        Numeric(10, 2), nullable=False, comment="Bonus amount (+/- value)"
    )
    balance_before = Column(
        Numeric(10, 2), nullable=False, comment="Client bonus balance before operation"
    )
    balance_after = Column(
        Numeric(10, 2), nullable=False, comment="Client bonus balance after operation"
    )

    # Operation details
    description = Column(Text, nullable=True, comment="Operation description")

    # For EARN operations
    bonus_percent = Column(
        Numeric(5, 2), nullable=True, comment="Bonus percentage applied"
    )
    transaction_sum = Column(
        Numeric(10, 2), nullable=True, comment="Transaction sum for bonus calculation"
    )

    # System fields
    processed_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, comment="When operation was processed"
    )

    # Relationships
    client_details = relationship("Client", back_populates="bonus_history")
    transaction_details = relationship("Transaction", back_populates="bonus_operations")

    def __repr__(self):
        return f"<TransactionBonus client_id={self.client_id} type={self.operation_type} amount={self.amount}>"
