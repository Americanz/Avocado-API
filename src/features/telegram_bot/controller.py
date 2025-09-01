"""
Telegram Bot Controller

Internal API endpoints for telegram bot management.
Not exposed to external users.
"""

from typing import List, Optional
from fastapi import status
from sqlalchemy.orm import Session

from src.core.crud.crud_base import CRUDBase
from .models import Client, TelegramBonusAccount, TelegramBonusTransaction
from .schemas import (
    ClientCreate,
    ClientUpdate,
    TelegramBonusAccountCreate,
    TelegramBonusAccountUpdate,
    TelegramBonusTransactionCreate,
    # Legacy imports for backward compatibility
    TelegramBotUserCreate,
    TelegramBotUserUpdate,
)


class TelegramBotUserController(CRUDBase[Client, ClientCreate, ClientUpdate]):
    """Controller for Telegram Bot Users (now using Client)"""

    def get_by_telegram_id(
        self, db: Session, telegram_user_id: int
    ) -> Optional[Client]:
        """Get user by telegram user ID"""
        return (
            db.query(Client).filter(Client.telegram_user_id == telegram_user_id).first()
        )

    def get_users_with_phone(self, db: Session, limit: int = 100) -> List[Client]:
        """Get users that have shared their phone number"""
        return db.query(Client).filter(Client.phone.isnot(None)).limit(limit).all()

    def get_blocked_users(self, db: Session, limit: int = 100) -> List[Client]:
        """Get blocked users"""
        return (
            db.query(Client)
            .filter(Client.is_telegram_active == False)
            .limit(limit)
            .all()
        )


class TelegramBonusAccountController(
    CRUDBase[
        TelegramBonusAccount, TelegramBonusAccountCreate, TelegramBonusAccountUpdate
    ]
):
    """Controller for Telegram Bonus Accounts"""

    def get_by_client_id(
        self, db: Session, client_id: int
    ) -> Optional[TelegramBonusAccount]:
        """Get bonus account by client ID"""
        return (
            db.query(TelegramBonusAccount)
            .filter(TelegramBonusAccount.client_id == client_id)
            .first()
        )

    def get_accounts_with_balance(
        self, db: Session, min_balance: int = 1, limit: int = 100
    ) -> List[TelegramBonusAccount]:
        """Get accounts with balance above threshold"""
        return (
            db.query(TelegramBonusAccount)
            .filter(TelegramBonusAccount.balance >= min_balance)
            .limit(limit)
            .all()
        )

    def add_bonus(
        self,
        db: Session,
        client_id: int,
        amount: int,
        reason: str = None,
        admin_id: int = None,
    ) -> TelegramBonusAccount:
        """Add bonus to account"""
        account = self.get_by_client_id(db, client_id)

        if not account:
            # Create new account
            account = TelegramBonusAccount(client_id=client_id, balance=amount)
            db.add(account)
        else:
            # Update existing account
            account.balance += amount

        # Create transaction record
        transaction = TelegramBonusTransaction(
            client_id=client_id,
            amount=amount,
            type="accrual",
            description=reason or "Bonus added",
            admin_id=admin_id,
        )
        db.add(transaction)
        db.commit()
        db.refresh(account)

        return account


class TelegramBonusTransactionController(
    CRUDBase[
        TelegramBonusTransaction,
        TelegramBonusTransactionCreate,
        TelegramBonusTransactionCreate,
    ]
):
    """Controller for Telegram Bonus Transactions"""

    def get_by_client_id(
        self, db: Session, client_id: int, limit: int = 50
    ) -> List[TelegramBonusTransaction]:
        """Get transactions for specific client"""
        return (
            db.query(TelegramBonusTransaction)
            .filter(TelegramBonusTransaction.client_id == client_id)
            .order_by(TelegramBonusTransaction.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_recent_transactions(
        self, db: Session, limit: int = 100
    ) -> List[TelegramBonusTransaction]:
        """Get recent transactions for all clients"""
        return (
            db.query(TelegramBonusTransaction)
            .order_by(TelegramBonusTransaction.created_at.desc())
            .limit(limit)
            .all()
        )


# Create controller instances
telegram_bot_user = TelegramBotUserController(Client)
telegram_bonus_account = TelegramBonusAccountController(TelegramBonusAccount)
telegram_bonus_transaction = TelegramBonusTransactionController(
    TelegramBonusTransaction
)


__all__ = [
    "TelegramBotUserController",
    "TelegramBonusAccountController",
    "TelegramBonusTransactionController",
    "telegram_bot_user",
    "telegram_bonus_account",
    "telegram_bonus_transaction",
]
