"""
Price model for product pricing management.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import relationship

from src.core.models.base_model import BaseModel


class Price(BaseModel):
    """Price model for product pricing."""

    __tablename__ = "prices"

    name = Column(String, nullable=False)
    price_value = Column(Float, nullable=False, default=0.0)
    is_active = Column(Boolean, default=True, nullable=False)
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_to = Column(DateTime, nullable=True)

    # Price type (regular, sale, wholesale, etc.)
    price_type = Column(String, nullable=False, default="regular")

    # Foreign keys
    product_id = Column(PgUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)

    # Relationships
    product = relationship("Product", back_populates="prices")

    def __repr__(self) -> str:
        return f"<Price {self.price_type} {self.price_value} for {self.product_id}>"
