"""
Telegram Bot Receipt Service Functions
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from ..models import Client, Transaction, TransactionProduct


# Service functions for receipt operations
def get_user_receipts(
    session: Session, telegram_user_id: int, limit: int = 10
) -> List[Dict[str, Any]]:
    """Get user receipts as dicts"""
    # Get user first
    client = (
        session.query(Client)
        .filter(Client.telegram_user_id == telegram_user_id)
        .first()
    )

    if not client or not client.phone:
        return []

    # Get transactions
    transactions = (
        session.query(Transaction)
        .filter(Transaction.client_phone == client.phone)
        .order_by(Transaction.date_close.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": str(t.id),
            "receipt_number": str(t.transaction_id),
            "user_id": telegram_user_id,
            "store_name": t.spot_name,
            "total_amount": float(t.sum),
            "discount": float(t.discount),
            "date_created": t.date_close or t.created_at,
        }
        for t in transactions
    ]


def get_receipt_details(session: Session, receipt_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed receipt information"""
    try:
        transaction_id = int(receipt_id)
    except ValueError:
        return None

    transaction = (
        session.query(Transaction)
        .filter(Transaction.transaction_id == transaction_id)
        .first()
    )

    if not transaction:
        return None

    # Get transaction items
    items = (
        session.query(TransactionProduct)
        .filter(TransactionProduct.transaction_id == transaction_id)
        .all()
    )

    return {
        "transaction_id": transaction.transaction_id,
        "spot_name": transaction.spot_name,
        "date_close": transaction.date_close,
        "sum": float(transaction.sum),
        "discount": float(transaction.discount),
        "status": transaction.status,
        "client_phone": transaction.client_phone,
        "items": [
            {
                "id": str(item.id),
                "receipt_id": str(item.transaction_id),
                "product_name": item.product_details.product_name if item.product_details else "Unknown Product",
                "category_name": item.category_name,
                "quantity": float(item.count),
                "price": float(item.price),
                "total_price": float(item.sum),
            }
            for item in items
        ],
        "raw_data": transaction.raw_data,
    }


def get_monthly_receipts_stats(
    session: Session, telegram_user_id: int, year: int, month: int
) -> Dict[str, Any]:
    """Get monthly statistics for user receipts"""
    # Get user first
    client = (
        session.query(Client)
        .filter(Client.telegram_user_id == telegram_user_id)
        .first()
    )

    if not client or not client.phone:
        return {"count": 0, "total_amount": 0, "total_discount": 0}

    # Get transactions for the month
    from sqlalchemy import extract, func

    transactions = (
        session.query(Transaction)
        .filter(
            Transaction.client_phone == client.phone,
            extract("year", Transaction.date_close) == year,
            extract("month", Transaction.date_close) == month,
        )
        .all()
    )

    total_amount = sum(float(t.sum) for t in transactions)
    total_discount = sum(float(t.discount) for t in transactions)

    return {
        "count": len(transactions),
        "total_amount": total_amount,
        "total_discount": total_discount,
        "receipts": [
            {
                "id": str(t.id),
                "receipt_number": str(t.transaction_id),
                "user_id": telegram_user_id,
                "store_name": t.spot_name,
                "total_amount": float(t.sum),
                "discount": float(t.discount),
                "date_created": t.date_close or t.created_at,
            }
            for t in transactions
        ],
    }


__all__ = ["get_user_receipts", "get_receipt_details", "get_monthly_receipts_stats"]
