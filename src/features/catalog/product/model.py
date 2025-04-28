"""
Product model for catalog management.
"""



from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import relationship

from src.core.models.base_model import BaseModel


class Product(BaseModel):
    """Product model for catalog."""

    __tablename__ = "products"

    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    sku = Column(String, nullable=True, unique=True, index=True)
    barcode = Column(String, nullable=True, index=True)
    price = Column(Float, nullable=False, default=0.0)
    cost_price = Column(Float, nullable=True)
    tax_rate = Column(Float, nullable=True, default=0.0)
    is_active = Column(Boolean, default=True, nullable=False)
    stock_quantity = Column(Integer, default=0, nullable=False)
    min_stock_quantity = Column(Integer, default=0, nullable=True)

    # Foreign keys
    category_id = Column(
        PgUUID(as_uuid=True), ForeignKey("categories.id"), nullable=True
    )

    # Relationships - статично оголошуємо прямо в класі
    category = relationship("Category", back_populates="products")
    prices = relationship(
        "Price", back_populates="product", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Product {self.name}>"
