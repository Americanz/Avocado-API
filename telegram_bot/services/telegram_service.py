"""
Telegram Service Adapter

This service provides a clean interface for telegram bot handlers
to work with the unified database models through adapter schemas.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from telegram_bot.schemas import (
    TelegramBotUserAdapter,
    TelegramReceiptAdapter,
    TelegramProductAdapter,
    get_telegram_user,
    get_user_receipts,
    create_or_update_telegram_user,
)

from src.features.telegram_bot.models import (
    Client,
    Transaction,
    Product,
    TelegramBonusAccount,
    TelegramBonusTransaction,
)


class TelegramUserService:
    """Service for telegram user operations"""

    def __init__(self, session: Session):
        self.session = session

    def get_user_by_id(self, user_id: int) -> Optional[TelegramBotUserAdapter]:
        """Get user by Telegram ID"""
        return get_telegram_user(self.session, user_id)

    def upsert_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        language_code: Optional[str] = None,
    ) -> TelegramBotUserAdapter:
        """Create or update user"""
        return create_or_update_telegram_user(
            self.session, user_id, username, first_name, last_name, phone, language_code
        )

    def search_users(self, query: str) -> List[TelegramBotUserAdapter]:
        """Search users by username, name, or phone"""
        clients = (
            self.session.query(Client)
            .filter(
                (Client.telegram_username.ilike(f"%{query}%"))
                | (Client.telegram_first_name.ilike(f"%{query}%"))
                | (Client.telegram_last_name.ilike(f"%{query}%"))
                | (Client.phone.ilike(f"%{query}%"))
            )
            .limit(10)
            .all()
        )

        return [TelegramBotUserAdapter.from_client(client) for client in clients]


class TelegramReceiptService:
    """Service for receipt operations"""

    def __init__(self, session: Session):
        self.session = session

    def get_user_receipts(
        self, user_id: int, limit: int = 10
    ) -> List[TelegramReceiptAdapter]:
        """Get user receipts"""
        return get_user_receipts(self.session, user_id, limit)

    def get_receipt_details(self, receipt_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed receipt information"""
        try:
            transaction_id = int(receipt_id)
        except ValueError:
            return None

        transaction = (
            self.session.query(Transaction)
            .filter(Transaction.transaction_id == transaction_id)
            .first()
        )

        if not transaction:
            return None

        return {
            "transaction_id": transaction.transaction_id,
            "spot_name": transaction.spot_name,
            "date_close": transaction.date_close,
            "sum": float(transaction.sum),
            "discount": float(transaction.discount),
            "status": transaction.status,
            "client_phone": transaction.client_phone,
            "raw_data": transaction.raw_data,
        }


class TelegramBonusService:
    """Service for bonus operations with backward compatibility"""

    def __init__(self, session: Session):
        self.session = session

    def get_user_balance(self, user_id: int) -> int:
        """Get user bonus balance"""
        account = (
            self.session.query(TelegramBonusAccount)
            .filter(TelegramBonusAccount.client_id == user_id)
            .first()
        )

        return account.balance if account else 0

    def create_or_get_bonus_account(self, user_id: int) -> TelegramBonusAccount:
        """Create bonus account if doesn't exist"""
        account = (
            self.session.query(TelegramBonusAccount)
            .filter(TelegramBonusAccount.client_id == user_id)
            .first()
        )

        if not account:
            account = TelegramBonusAccount(client_id=user_id, balance=0)
            self.session.add(account)
            self.session.flush()

        return account

    def add_bonus(
        self,
        user_id: int,
        amount: int,
        reason: str = None,
        admin_id: int = None,
        poster_transaction_id: int = None,
    ) -> bool:
        """Add bonuses to user account"""
        try:
            # Get or create account
            account = self.create_or_get_bonus_account(user_id)
            account.balance += amount
            account.updated_at = datetime.utcnow()

            # Create transaction record
            transaction = TelegramBonusTransaction(
                client_id=user_id,
                amount=amount,
                type="accrual",
                description=reason or f"Нарахування {amount} бонусів",
                admin_id=admin_id,
                poster_transaction_id=poster_transaction_id,
            )
            self.session.add(transaction)
            self.session.commit()

            return True
        except Exception:
            self.session.rollback()
            return False

    def get_user_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user bonus history"""
        transactions = (
            self.session.query(TelegramBonusTransaction)
            .filter(TelegramBonusTransaction.client_id == user_id)
            .order_by(TelegramBonusTransaction.created_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "amount": trans.amount,
                "type": trans.type,
                "description": trans.description,
                "created_at": trans.created_at,
            }
            for trans in transactions
        ]


# Factory function to create services
def get_telegram_services(session: Session) -> Dict[str, Any]:
    """Get all telegram services"""
    return {
        "user": TelegramUserService(session),
        "receipt": TelegramReceiptService(session),
        "bonus": TelegramBonusService(session),
    }


__all__ = [
    "TelegramUserService",
    "TelegramReceiptService",
    "TelegramBonusService",
    "get_telegram_services",
]
