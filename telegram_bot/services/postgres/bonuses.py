"""
PostgreSQL Bonus Service for Telegram Bot
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy import desc
from src.features.telegram_bot.models import (
    Client as Client,
    TelegramBonusAccount as BonusAccount,
    TelegramBonusTransaction as Transaction,
    TelegramStore as Store,
    Transaction as Receipt,
    Product as Product,
    TransactionProduct as PurchaseHistory,
)
from .base import PostgresBaseService

logger = logging.getLogger("telegram_bot.postgres.bonuses")


class PostgresBonusService(PostgresBaseService):
    """PostgreSQL Bonus Service"""

    def get_user_balance(self, user_id: int) -> int:
        """Get user bonus balance"""

        def query(db):
            account = (
                db.query(BonusAccount).filter(BonusAccount.client_id == user_id).first()
            )
            return account.balance if account else 0

        return self.execute_query(query)

    def create_or_get_bonus_account(self, user_id: int):
        """Create bonus account if doesn't exist"""

        def query(db):
            account = (
                db.query(BonusAccount).filter(BonusAccount.client_id == user_id).first()
            )

            if not account:
                account = BonusAccount(client_id=user_id, balance=0)
                db.add(account)
                db.flush()
                logger.info(f"Created bonus account for user {user_id}")

            return account

        return self.execute_query(query)

    def add_bonus(
        self,
        user_id: int,
        amount: int,
        reason: str = None,
        admin_id: int = None,
        store_id: str = None,
        receipt_id: str = None,
    ) -> bool:
        """Add bonuses to user account with optional store and receipt information"""

        def query(db):
            # Get or create account
            account = (
                db.query(BonusAccount).filter(BonusAccount.client_id == user_id).first()
            )
            if not account:
                account = BonusAccount(client_id=user_id, balance=amount)
                db.add(account)
            else:
                account.balance += amount
                account.updated_at = datetime.utcnow()

            # Create transaction record with store and receipt info
            transaction = Transaction(
                client_id=user_id,
                amount=amount,
                type="accrual",
                description=reason or f"Нарахування {amount} бонусів",
                admin_id=admin_id,
                store_id=store_id,
                receipt_id=receipt_id,
            )
            db.add(transaction)

            logger.info(
                f"Added {amount} bonuses to user {user_id}, store: {store_id}, receipt: {receipt_id}"
            )
            return True

        return self.execute_query(query)

    def remove_bonus(
        self, user_id: int, amount: int, reason: str = None, admin_id: int = None
    ) -> bool:
        """Remove bonuses from user account"""

        def query(db):
            account = (
                db.query(BonusAccount).filter(BonusAccount.client_id == user_id).first()
            )

            if not account or account.balance < amount:
                logger.warning(
                    f"Insufficient balance for user {user_id}: {account.balance if account else 0} < {amount}"
                )
                return False

            account.balance -= amount
            account.updated_at = datetime.utcnow()

            # Create transaction record
            transaction = Transaction(
                client_id=user_id,
                amount=-amount,  # Negative for debit
                type="debit",
                description=reason or f"Списання {amount} бонусів",
                admin_id=admin_id,
            )
            db.add(transaction)

            logger.info(f"Removed {amount} bonuses from user {user_id}")
            return True

        return self.execute_query(query)

    def get_user_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user bonus history with store and receipt information"""

        def query(db):
            # Join with stores and receipts to get full information
            transactions = (
                db.query(Transaction, Store, Receipt)
                .outerjoin(Store, Transaction.store_id == Store.id)
                .outerjoin(
                    Receipt,
                    Transaction.poster_transaction_id == Receipt.transaction_id,
                )
                .filter(Transaction.client_id == user_id)
                .order_by(desc(Transaction.created_at))
                .limit(limit)
                .all()
            )

            result = []
            for trans, store, receipt in transactions:
                item = {
                    "amount": trans.amount,
                    "type": trans.type,
                    "description": trans.description,
                    "created_at": trans.created_at,
                    "store_name": store.name if store else None,
                    "store_address": store.address if store else None,
                    "receipt_number": receipt.transaction_id if receipt else None,
                    "receipt_total": float(receipt.sum) if receipt else None,
                }
                result.append(item)

            return result

        return self.execute_query(query)

    def get_bonus_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent bonus history for all users with store and receipt information"""

        def query(db):
            transactions = (
                db.query(Transaction, Client, Store, Receipt)
                .join(Client, Transaction.client_id == Client.telegram_user_id)
                .outerjoin(Store, Transaction.store_id == Store.id)
                .outerjoin(
                    Receipt,
                    Transaction.poster_transaction_id == Receipt.transaction_id,
                )
                .order_by(desc(Transaction.created_at))
                .limit(limit)
                .all()
            )

            result = []
            for trans, user, store, receipt in transactions:
                item = {
                    "client_id": trans.client_id,
                    "username": user.telegram_username,
                    "first_name": user.telegram_first_name,
                    "amount": trans.amount,
                    "type": trans.type,
                    "description": trans.description,
                    "created_at": trans.created_at,
                    "store_name": store.name if store else None,
                    "store_address": store.address if store else None,
                    "receipt_number": receipt.transaction_id if receipt else None,
                    "receipt_total": float(receipt.sum) if receipt else None,
                }
                result.append(item)

            return result

        return self.execute_query(query)

    def get_users_with_bonuses_count(self) -> int:
        """Get count of users with bonus accounts"""

        def query(db):
            return db.query(BonusAccount).filter(BonusAccount.balance > 0).count()

        return self.execute_query(query)

    def table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        try:
            with self.get_session() as db:
                # Try to query the table
                if table_name in ["clients", "bot_users", "telegram_bot_users"]:
                    db.query(Client).limit(1).all()
                elif table_name in ["telegram_bonus_accounts", "bonuses"]:
                    db.query(BonusAccount).limit(1).all()
                elif table_name in [
                    "telegram_bonus_transactions",
                    "bonus_transactions",
                ]:
                    db.query(Transaction).limit(1).all()
                return True
        except Exception:
            return False

    def get_product_categories(self) -> List[str]:
        """Get all product categories from Poster products"""

        def query(db):
            categories = (
                db.query(Product.category_name)
                .filter(Product.category_name.isnot(None))
                .filter(Product.is_active == True)
                .distinct()
                .all()
            )
            return [cat[0] for cat in categories if cat[0]]

        return self.execute_query(query)

    def get_purchase_history(
        self, user_id: int, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get user purchase history from Poster transactions"""

        def query(db):
            # Get user by telegram_user_id
            user = db.query(Client).filter(Client.telegram_user_id == user_id).first()
            if not user or not user.phone:
                return []

            # Get transactions for this user's phone
            transactions = (
                db.query(Receipt)
                .filter(Receipt.client_phone == user.phone)
                .order_by(desc(Receipt.date_close))
                .limit(limit)
                .all()
            )

            result = []
            for transaction in transactions:
                item = {
                    "transaction_id": transaction.transaction_id,
                    "spot_name": transaction.spot_name,
                    "date_close": transaction.date_close,
                    "total_amount": float(transaction.sum),
                    "discount": float(transaction.discount),
                    "status": transaction.status,
                }
                result.append(item)

            return result

        return self.execute_query(query)
