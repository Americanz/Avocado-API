"""
Order models for sales management.
"""

from datetime import datetime
from enum import Enum


from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLAlchemyEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID


from src.core.models.base_model import BaseModel


class OrderStatus(str, Enum):
    """Order status enum."""

    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class PaymentStatus(str, Enum):
    """Payment status enum."""

    PENDING = "pending"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    REFUNDED = "refunded"
    FAILED = "failed"


class Order(BaseModel):
    """Order model for sales."""

    __tablename__ = "orders"

    order_number = Column(String, nullable=False, unique=True, index=True)
    total_amount = Column(Float, nullable=False, default=0.0)
    tax_amount = Column(Float, nullable=True, default=0.0)
    discount_amount = Column(Float, nullable=True, default=0.0)
    shipping_amount = Column(Float, nullable=True, default=0.0)
    status = Column(
        SQLAlchemyEnum(OrderStatus), nullable=False, default=OrderStatus.DRAFT
    )
    payment_status = Column(
        SQLAlchemyEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING
    )
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Dates
    order_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    payment_date = Column(DateTime, nullable=True)
    shipping_date = Column(DateTime, nullable=True)
    delivery_date = Column(DateTime, nullable=True)

    # Foreign keys
    client_id = Column(PgUUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)


    def __repr__(self) -> str:
        return f"<Order {self.order_number}>"


class OrderItem(BaseModel):
    """Order item model for order line items."""

    __tablename__ = "order_items"

    quantity = Column(Integer, nullable=False, default=1)
    price = Column(Float, nullable=False)
    discount = Column(Float, nullable=True, default=0.0)
    total = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)

    # Foreign keys
    order_id = Column(PgUUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    product_id = Column(PgUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)



    def __repr__(self) -> str:
        return f"<OrderItem {self.product_id} x {self.quantity}>"
