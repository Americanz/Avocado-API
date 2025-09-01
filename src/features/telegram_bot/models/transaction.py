"""
Poster transaction model
"""

from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    Text,
    BigInteger,
    ForeignKey,
    Numeric,
    JSON,
)
from sqlalchemy.orm import relationship
from src.core.models.base_model import BaseModel


class Transaction(BaseModel):
    """
    Poster transaction data from API
    Maps to getTransactions API response
    """

    __tablename__ = "transactions"

    use_generic_routes = True
    search_fields = ["transaction_id", "client_phone", "spot_name"]
    default_order_by = ["-date_close"]

    # Basic transaction info
    transaction_id = Column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True,
        comment="Poster transaction ID",
    )
    spot_id = Column(Integer, nullable=False, comment="Spot ID from Poster")

    # Link to Poster spot
    spot = Column(
        BigInteger,
        ForeignKey("spots.spot_id"),
        nullable=True,
        comment="Link to Poster spot",
    )

    # Client information
    client_id = Column(BigInteger, nullable=True, comment="Poster client ID")

    # Link to Poster client
    client = Column(
        BigInteger,
        ForeignKey("clients.client_id"),
        nullable=True,
        comment="Link to Poster client",
    )

    # Transaction details
    table_id = Column(Integer, nullable=True, comment="Table ID")

    # Dates and times
    date_start = Column(DateTime, nullable=True, comment="Transaction start time")
    date_close = Column(
        DateTime, nullable=True, index=True, comment="Transaction close time"
    )

    # Financial data
    sum = Column(Numeric(10, 2), nullable=False, comment="Total transaction sum")

    # Payment details
    payed_sum = Column(Numeric(10, 2), nullable=True, default=0, comment="Total payment amount")
    payed_cash = Column(Numeric(10, 2), nullable=True, default=0, comment="Cash payment amount")
    payed_card = Column(Numeric(10, 2), nullable=True, default=0, comment="Card payment amount")
    payed_cert = Column(Numeric(10, 2), nullable=True, default=0, comment="Certificate payment amount")
    payed_bonus = Column(Numeric(10, 2), nullable=True, default=0, comment="Bonus payment amount")
    payed_third_party = Column(Numeric(10, 2), nullable=True, default=0, comment="Third party payment amount")
    round_sum = Column(Numeric(10, 2), nullable=True, default=0, comment="Rounding amount")

    # Payment type and reason
    pay_type = Column(Integer, nullable=True, comment="Payment type: 0-no payment, 1-cash, 2-card, 3-mixed")
    reason = Column(Integer, nullable=True, comment="Reason for closing without payment")

    # Additional charges
    tip_sum = Column(Numeric(10, 2), nullable=True, default=0, comment="Service tip amount")

    # Discounts and bonuses
    discount = Column(Numeric(10, 2), nullable=False, default=0, comment="Discount percentage")
    bonus = Column(Numeric(10, 2), nullable=False, default=0, comment="Bonus percentage")

    # Fiscal information
    print_fiscal = Column(Integer, nullable=True, default=0, comment="Fiscal print flag: 0-no, 1-yes, 2-return")

    # Status and type
    status = Column(Integer, nullable=False, comment="Transaction status")

    # Staff information
    user_id = Column(
        Text, nullable=True, comment="Poster user ID who created transaction"
    )

    # Raw API response for debugging
    raw_data = Column(JSON, nullable=True, comment="Raw API response data")

    sync_error = Column(Text, nullable=True, comment="Last sync error")
    last_sync_attempt = Column(
        DateTime, nullable=True, comment="Last sync attempt time"
    )

    # Relationships
    client_details = relationship("Client", foreign_keys=[client], back_populates=None)
    spot_details = relationship(
        "Spot",
        back_populates="transactions",
        foreign_keys=[spot_id],
        primaryjoin="Transaction.spot_id == Spot.spot_id",
        viewonly=True,
    )
    products = relationship("TransactionProduct", back_populates="transaction")

    bonus_operations = relationship("TransactionBonus", back_populates="transaction_details")

    def __repr__(self):
        return f"<Transaction transaction_id={self.transaction_id} sum={self.sum}>"
