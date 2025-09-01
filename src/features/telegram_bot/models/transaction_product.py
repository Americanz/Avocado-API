"""
Poster transaction product model
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    BigInteger,
    ForeignKey,
    Numeric,
)
from sqlalchemy.orm import relationship
from src.core.models.base_model import BaseModel


class TransactionProduct(BaseModel):
    """
    Products in transaction
    Maps to products array in transaction details
    """

    __tablename__ = "transaction_products"

    use_generic_routes = False
    default_order_by = ["transaction_id", "position"]

    # Link to transaction
    transaction_id = Column(
        BigInteger,
        ForeignKey("transactions.transaction_id"),
        nullable=False,
        index=True,
        comment="Poster transaction ID",
    )

    # Product position in transaction
    position = Column(
        Integer, nullable=False, comment="Product position in transaction"
    )

    # Product details from Poster API
    poster_product_id = Column(Integer, nullable=True, comment="Poster product ID")

    # Link to Poster product catalog
    product = Column(
        BigInteger,
        ForeignKey("products.poster_product_id"),
        nullable=True,
        comment="Link to Poster product catalog",
    )

    # Pricing and quantity
    count = Column(Numeric(8, 3), nullable=False, comment="Product quantity")
    price = Column(Numeric(10, 2), nullable=False, comment="Product price per unit")
    sum = Column(Numeric(10, 2), nullable=False, comment="Total sum for this product")

    # Discounts and bonuses
    discount = Column(
        Numeric(10, 2), nullable=True, default=0, comment="Product discount"
    )
    bonus = Column(Numeric(10, 2), nullable=True, default=0, comment="Product bonus")

    # Printing status
    print = Column(
        Integer, nullable=True, default=1, comment="Print status: 0-no print, 1-print"
    )

    # Tax information
    tax_id = Column(Integer, nullable=True, comment="Tax ID")
    tax_value = Column(Numeric(10, 2), nullable=True, comment="Tax amount")
    tax_sum = Column(Numeric(10, 2), nullable=True, comment="Total tax amount")
    tax_type = Column(String(20), nullable=True, comment="Tax type")

    # Additional product data (transaction-specific only)
    weight_flag = Column(
        Integer, nullable=True, default=0, comment="Weight product flag"
    )
    barcode = Column(
        String(255), nullable=True, comment="Product barcode (if differs from catalog)"
    )

    # Relationships
    transaction = relationship("Transaction", back_populates="products")
    product_details = relationship("Product", foreign_keys=[product])

    def __repr__(self):
        return f"<TransactionProduct transaction_id={self.transaction_id} product_id={self.product}>"
