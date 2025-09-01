"""
Poster spot/establishment model
"""

from sqlalchemy import (
    Column,
    String,
    BigInteger,
    JSON,
)
from sqlalchemy.orm import relationship
from src.core.models.base_model import BaseModel


class Spot(BaseModel):
    """Model for Poster spots/establishments"""

    __tablename__ = "spots"

    # Poster spot info - тільки 3 поля з API
    spot_id = Column(
        BigInteger, nullable=False, unique=True, index=True, comment="Spot ID"
    )
    name = Column(String(255), nullable=False, comment="Spot name")
    address = Column(String(500), nullable=True, comment="Spot address")

    # Store raw API response
    raw_data = Column(JSON, nullable=True, comment="Original API response data")

    # Relationships
    transactions = relationship(
        "Transaction",
        back_populates="spot_details",
        foreign_keys="Transaction.spot_id",
        primaryjoin="Spot.spot_id == Transaction.spot_id",
        viewonly=True,
    )

    def __repr__(self):
        return f"<Spot id={self.spot_id} name='{self.name}'>"
