"""
PostgreSQL User Service for Telegram Bot
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from src.features.telegram_bot.models import Client as Client
from .base import PostgresBaseService

logger = logging.getLogger("telegram_bot.postgres.user")


class PostgresUserService(PostgresBaseService):
    """PostgreSQL User Service"""

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by Telegram ID"""

        def query(db):
            user = db.query(Client).filter(Client.telegram_user_id == user_id).first()
            if user:
                return {
                    "user_id": user.telegram_user_id,
                    "username": user.telegram_username,
                    "first_name": user.telegram_first_name,
                    "last_name": user.telegram_last_name,
                    "phone": user.phone,
                    "is_active": user.is_active,
                    "language_code": user.language_code,
                    "created_at": user.created_at,
                }
            return None

        return self.execute_query(query)

    def upsert_user(
        self,
        user_id: int,
        username: str = None,
        first_name: str = None,
        last_name: str = None,
        phone: str = None,
    ) -> Dict[str, Any]:
        """Create or update user"""

        def query(db):
            user = db.query(Client).filter(Client.telegram_user_id == user_id).first()

            if user:
                # Update existing user
                if username is not None:
                    user.telegram_username = username
                if first_name is not None:
                    user.telegram_first_name = first_name
                if last_name is not None:
                    user.telegram_last_name = last_name
                if phone is not None:
                    user.phone = phone
                user.updated_at = datetime.utcnow()
            else:
                # Create new user
                user = Client(
                    telegram_user_id=user_id,
                    telegram_username=username,
                    telegram_first_name=first_name,
                    telegram_last_name=last_name,
                    phone=phone,
                    is_telegram_active=True,
                )
                db.add(user)

            db.flush()  # To get the updated user data
            logger.info(f"User upserted: {user_id}")
            return {
                "user_id": user.telegram_user_id,
                "username": user.telegram_username,
                "phone": user.phone,
                "created_at": user.created_at,
            }

        return self.execute_query(query)

    def search_users(self, query: str) -> list:
        """Search users by username, name, or phone"""

        def db_query(db):
            users = (
                db.query(Client)
                .filter(
                    (Client.telegram_username.ilike(f"%{query}%"))
                    | (Client.telegram_first_name.ilike(f"%{query}%"))
                    | (Client.telegram_last_name.ilike(f"%{query}%"))
                    | (Client.phone.ilike(f"%{query}%"))
                )
                .limit(10)
                .all()
            )

            return [
                {
                    "user_id": user.telegram_user_id,
                    "username": user.telegram_username,
                    "first_name": user.telegram_first_name,
                    "last_name": user.telegram_last_name,
                    "phone": user.phone,
                }
                for user in users
            ]

        return self.execute_query(db_query)
