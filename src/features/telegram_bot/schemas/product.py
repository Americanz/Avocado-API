"""
Telegram Bot Product Schema Adapter
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from sqlalchemy.orm import Session

from ..models import Product, Client, Transaction, TransactionProduct


class TelegramProduct(BaseModel):
    """Adapter schema for Product to be used as TelegramProduct"""

    # Telegram bot expects these field names
    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    brand: Optional[str] = Field(None, description="Brand")
    category: Optional[str] = Field(None, description="Category")
    base_price: Optional[float] = Field(None, description="Base price")
    barcode: Optional[str] = Field(None, description="Barcode")

    @classmethod
    def from_poster_product(cls, product: Product) -> "TelegramProduct":
        """Convert Product to TelegramProduct"""
        # Try to extract brand from product name (first word)
        brand = None
        if product.product_name:
            words = product.product_name.split()
            brand = words[0] if words else None

        return cls(
            id=str(product.id),
            name=product.product_name,
            brand=brand,
            category=product.category_name,
            base_price=float(product.cost) if product.cost else None,
            barcode=product.barcode,
        )

    class Config:
        from_attributes = True


class TelegramUserFavorite(BaseModel):
    """Schema for user favorite products (using Product as base)"""

    product_id: str = Field(..., description="Product ID")
    user_id: int = Field(..., description="User ID")
    notes: Optional[str] = Field(None, description="User notes")
    added_at: datetime = Field(..., description="Added at")

    # Product details
    product: TelegramProduct = Field(..., description="Product details")

    class Config:
        from_attributes = True


class TelegramPurchaseHistory(BaseModel):
    """Schema for user purchase history (using TransactionProduct as base)"""

    id: str = Field(..., description="Purchase ID")
    user_id: int = Field(..., description="User ID")
    product_name: str = Field(..., description="Product name")
    category_name: Optional[str] = Field(None, description="Category")
    store_name: Optional[str] = Field(None, description="Store name")
    quantity: float = Field(..., description="Quantity")
    unit_price: float = Field(..., description="Unit price")
    total_price: float = Field(..., description="Total price")
    discount: float = Field(0, description="Discount")
    purchase_date: datetime = Field(..., description="Purchase date")

    @classmethod
    def from_poster_transaction_product(
        cls,
        item: TransactionProduct,
        transaction: Transaction,
        user_id: int,
    ) -> "TelegramPurchaseHistory":
        """Convert TransactionProduct to TelegramPurchaseHistory"""
        return cls(
            id=str(item.id),
            user_id=user_id,
            product_name=item.product_name,
            category_name=item.category_name,
            store_name=transaction.spot_name,
            quantity=float(item.count),
            unit_price=float(item.price),
            total_price=float(item.sum),
            discount=float(item.discount),
            purchase_date=transaction.date_close or transaction.created_at,
        )

    class Config:
        from_attributes = True


# Service functions for product operations
def get_product_categories(session: Session) -> List[str]:
    """Get all product categories from Poster products"""
    categories = (
        session.query(Product.category_name)
        .filter(Product.category_name.isnot(None))
        .filter(Product.is_active == True)
        .distinct()
        .all()
    )
    return [cat[0] for cat in categories if cat[0]]


def search_products(
    session: Session, query: str, limit: int = 20
) -> List[TelegramProduct]:
    """Search products by name or category"""
    products = (
        session.query(Product)
        .filter(
            (Product.product_name.ilike(f"%{query}%"))
            | (Product.category_name.ilike(f"%{query}%"))
        )
        .filter(Product.is_active == True)
        .limit(limit)
        .all()
    )

    return [TelegramProduct.from_poster_product(product) for product in products]


def get_user_purchase_history(
    session: Session, telegram_user_id: int, limit: int = 20
) -> List[TelegramPurchaseHistory]:
    """Get user purchase history from Poster transactions"""
    # Get user by telegram_user_id
    user = (
        session.query(Client)
        .filter(Client.telegram_user_id == telegram_user_id)
        .first()
    )
    if not user or not user.phone:
        return []

    # Get transactions for this user's phone with items
    from sqlalchemy.orm import joinedload

    transactions = (
        session.query(Transaction)
        .filter(Transaction.client_phone == user.phone)
        .order_by(Transaction.date_close.desc())
        .limit(limit)
        .all()
    )

    purchase_history = []
    for transaction in transactions:
        # Get transaction items
        items = (
            session.query(TransactionProduct)
            .filter(TransactionProduct.transaction_id == transaction.transaction_id)
            .all()
        )

        for item in items:
            purchase_history.append(
                TelegramPurchaseHistory.from_poster_transaction_product(
                    item, transaction, telegram_user_id
                )
            )

    return purchase_history[:limit]  # Limit total items


def get_user_favorite_products(
    session: Session, telegram_user_id: int
) -> List[Dict[str, Any]]:
    """Get user's most purchased products as 'favorites'"""
    # Get user
    user = (
        session.query(Client)
        .filter(Client.telegram_user_id == telegram_user_id)
        .first()
    )
    if not user or not user.phone:
        return []

    # Get most purchased products
    from sqlalchemy import func, desc

    favorite_products = (
        session.query(
            Product.product_name,
            TransactionProduct.category_name,
            func.count(TransactionProduct.id).label("purchase_count"),
            func.sum(TransactionProduct.count).label("total_quantity"),
            func.avg(TransactionProduct.price).label("avg_price"),
        )
        .join(
            Transaction,
            TransactionProduct.transaction_id == Transaction.transaction_id,
        )
        .join(
            Product,
            TransactionProduct.product == Product.poster_product_id,
        )
        .filter(Transaction.client_phone == user.phone)
        .group_by(
            Product.product_name,
            TransactionProduct.category_name,
        )
        .order_by(desc("purchase_count"))
        .limit(10)
        .all()
    )

    result = []
    for product in favorite_products:
        result.append(
            {
                "product_name": product.product_name,
                "category_name": product.category_name,
                "purchase_count": product.purchase_count,
                "total_quantity": float(product.total_quantity),
                "avg_price": float(product.avg_price),
            }
        )

    return result


__all__ = [
    "get_product_categories",
    "search_products",
    "get_user_purchase_history",
    "get_user_favorite_products",
]
