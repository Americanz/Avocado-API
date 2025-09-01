"""
Utility functions for Poster integration
"""

from typing import Dict
from sqlalchemy.orm import Session
from datetime import datetime

from src.features.telegram_bot.models import (
    Client,
    Transaction,
    TransactionProduct,
    TelegramBonusAccount,
    TelegramBonusTransaction,
)


class PosterDataManager:
    """Manager for Poster data operations"""

    def __init__(self, session: Session):
        self.session = session

    def find_or_create_user_by_phone(self, phone: str, client_data: Dict) -> Client:
        """Find or create user by phone number"""
        user = self.session.query(Client).filter(Client.phone == phone).first()

        if not user:
            user = Client(
                client_id=client_data.get("client_id"),
                telegram_user_id=0,  # Will be updated when user starts bot
                phone=phone,
                firstname=client_data.get("firstname"),
                lastname=client_data.get("lastname"),
                email=client_data.get("email"),
                card_number=client_data.get("card_number"),
                raw_data=client_data,
                last_sync_from_poster=datetime.now(),
            )
            self.session.add(user)
            self.session.commit()

        return user

    def sync_poster_transaction(self, transaction_data: Dict) -> Transaction:
        """Sync single transaction from Poster"""
        existing = (
            self.session.query(Transaction)
            .filter(Transaction.transaction_id == transaction_data["transaction_id"])
            .first()
        )

        if existing:
            # Update existing
            existing.raw_data = transaction_data
            return existing

        # Create new
        transaction = Transaction(
            transaction_id=transaction_data["transaction_id"],
            client_id=transaction_data.get("client_id"),
            spot_id=transaction_data["spot_id"],
            date_close=(
                datetime.fromisoformat(transaction_data["date_close"])
                if transaction_data.get("date_close")
                else None
            ),
            sum=float(transaction_data["sum"]),
            discount=float(transaction_data.get("discount", 0)),
            status=transaction_data.get("status"),
            raw_data=transaction_data,
        )

        self.session.add(transaction)
        self.session.flush()  # Get ID

        # Sync transaction items
        for item_data in transaction_data.get("products", []):
            self._sync_transaction_item(transaction.transaction_id, item_data)

        return transaction

    def _sync_transaction_item(self, transaction_id: int, item_data: Dict):
        """Sync transaction item"""
        item = TransactionProduct(
            transaction_id=transaction_id,
            poster_product_id=item_data.get("product_id"),
            product_name=item_data["product_name"],
            category_name=item_data.get("category_name"),
            count=float(item_data["count"]),
            price=float(item_data["price"]),
            sum=float(item_data["sum"]),
            discount=float(item_data.get("discount", 0)),
        )
        self.session.add(item)

    def process_bonuses_for_transaction(
        self, transaction: Transaction, bonus_rate: float = 1.0
    ):
        """Process bonuses for a transaction"""
        if transaction.bonus_processed:
            return

        # Find linked user
        user = None
        if transaction.client_phone:
            user = (
                self.session.query(Client)
                .filter(Client.phone == transaction.client_phone)
                .first()
            )

        if not user:
            return  # Can't award bonuses without user

        # Calculate bonus amount
        bonus_amount = int(transaction.sum * bonus_rate)

        if bonus_amount > 0:
            # Update bonus account
            account = (
                self.session.query(TelegramBonusAccount)
                .filter(TelegramBonusAccount.client_id == user.telegram_user_id)
                .first()
            )

            if not account:
                account = TelegramBonusAccount(
                    client_id=user.telegram_user_id,
                )
                self.session.add(account)

            account.balance += bonus_amount

            # Create bonus transaction
            bonus_transaction = TelegramBonusTransaction(
                client_id=user.telegram_user_id,
                amount=bonus_amount,
                type="accrual",
                description=f"Бонуси за покупку на {transaction.sum} грн",
                poster_transaction_id=transaction.transaction_id,
            )
            self.session.add(bonus_transaction)

        # Mark as processed
        transaction.bonus_processed = True
        self.session.commit()
