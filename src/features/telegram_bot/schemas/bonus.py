"""
Telegram Bot Bonus Service Functions
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from ..models import Client


# Service functions for bonus operations
def get_user_bonus_balance(session: Session, telegram_user_id: int) -> float:
    """Get user bonus balance from Client"""
    client = (
        session.query(Client)
        .filter(Client.telegram_user_id == telegram_user_id)
        .first()
    )

    return float(client.bonus) if client and client.bonus else 0.0


def create_or_get_bonus_account(
    session: Session, telegram_user_id: int
) -> Dict[str, Any]:
    """Get bonus account info (just returns user data)"""
    client = (
        session.query(Client)
        .filter(Client.telegram_user_id == telegram_user_id)
        .first()
    )

    if not client:
        return {"balance": 0.0, "user_id": telegram_user_id}

    return {
        "balance": float(client.bonus) if client.bonus else 0.0,
        "user_id": telegram_user_id,
        "client_id": str(client.id),
        "updated_at": client.updated_at,
    }


def add_bonus_to_user(
    session: Session,
    telegram_user_id: int,
    amount: float,
    reason: str = None,
    admin_id: int = None,
    poster_transaction_id: int = None,
) -> bool:
    """Add bonuses to user account (updates Client.bonus)"""
    try:
        client = (
            session.query(Client)
            .filter(Client.telegram_user_id == telegram_user_id)
            .first()
        )

        if not client:
            return False

        # Update bonus balance
        current_bonus = float(client.bonus) if client.bonus else 0.0
        client.bonus = current_bonus + amount
        client.updated_at = datetime.utcnow()

        session.commit()
        return True
    except Exception:
        session.rollback()
        return False


def remove_bonus_from_user(
    session: Session,
    telegram_user_id: int,
    amount: float,
    reason: str = None,
    admin_id: int = None,
) -> bool:
    """Remove bonuses from user account (updates Client.bonus)"""
    try:
        client = (
            session.query(Client)
            .filter(Client.telegram_user_id == telegram_user_id)
            .first()
        )

        if not client:
            return False

        current_bonus = float(client.bonus) if client.bonus else 0.0

        if current_bonus < amount:
            return False

        # Update bonus balance
        client.bonus = current_bonus - amount
        client.updated_at = datetime.utcnow()

        session.commit()
        return True
    except Exception:
        session.rollback()
        return False


def get_user_bonus_history(
    session: Session, telegram_user_id: int, limit: int = 10
) -> List[Dict[str, Any]]:
    """Get user bonus history (simplified - just shows current balance)"""
    client = (
        session.query(Client)
        .filter(Client.telegram_user_id == telegram_user_id)
        .first()
    )

    if not client:
        return []

    # Since we removed bonus transactions table, return basic info
    current_bonus = float(client.bonus) if client.bonus else 0.0

    return (
        [
            {
                "amount": current_bonus,
                "type": "balance",
                "description": f"Поточний баланс: {current_bonus} бонусів",
                "created_at": client.updated_at or client.created_at,
            }
        ]
        if current_bonus > 0
        else []
    )


def get_users_with_bonuses(
    session: Session, min_balance: float = 1.0, limit: int = 100
) -> List[Dict[str, Any]]:
    """Get users with bonus balances from Client"""
    from sqlalchemy import desc

    clients = (
        session.query(Client)
        .filter(Client.bonus >= min_balance)
        .filter(Client.telegram_user_id.isnot(None))
        .order_by(desc(Client.bonus))
        .limit(limit)
        .all()
    )

    result = []
    for client in clients:
        result.append(
            {
                "user_id": client.telegram_user_id,
                "username": client.telegram_username,
                "first_name": client.telegram_first_name,
                "phone": client.phone,
                "balance": float(client.bonus) if client.bonus else 0.0,
                "last_updated": client.updated_at,
            }
        )

    return result


def get_bonus_statistics(session: Session) -> Dict[str, Any]:
    """Get bonus system statistics from Client"""
    from sqlalchemy import func

    # Total clients with telegram_user_id
    total_accounts = (
        session.query(Client).filter(Client.telegram_user_id.isnot(None)).count()
    )

    # Clients with bonus balance
    accounts_with_balance = (
        session.query(Client)
        .filter(Client.bonus > 0, Client.telegram_user_id.isnot(None))
        .count()
    )

    # Total bonus amount
    total_balance = (
        session.query(func.sum(Client.bonus))
        .filter(Client.telegram_user_id.isnot(None))
        .scalar()
        or 0
    )

    return {
        "total_accounts": total_accounts,
        "accounts_with_balance": accounts_with_balance,
        "total_balance": float(total_balance),
        "recent_transactions_count": 0,  # No transactions table anymore
    }


__all__ = [
    "get_user_bonus_balance",
    "create_or_get_bonus_account",
    "add_bonus_to_user",
    "remove_bonus_from_user",
    "get_user_bonus_history",
    "get_users_with_bonuses",
    "get_bonus_statistics",
]
