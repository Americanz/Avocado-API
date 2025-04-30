"""
Модель для зберігання інформації про автентифікацію через Telegram.
"""

import pytz
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, BigInteger
from sqlalchemy.dialects.postgresql import UUID

from src.core.models.base_model import BaseModel
from src.config.settings import settings


class TelegramAuth(BaseModel):
    """
    Модель для зберігання інформації про автентифікацію через Telegram.

    Attributes:
        auth_code: Унікальний код автентифікації
        email: Email користувача (для прив'язки до аккаунту)
        telegram_id: ID користувача в Telegram (якщо відомий)
        telegram_username: Username користувача в Telegram (якщо відомий)
        is_used: Чи був використаний код автентифікації
        expires_at: Час закінчення терміну дії коду
        processed_at: Час обробки коду
    """

    __tablename__ = "telegram_auth"

    # Поля моделі (id, created_at, updated_at та is_active наслідуються від BaseModel)
    auth_code = Column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        comment="Унікальний код автентифікації",
    )
    email = Column(String(255), index=True, nullable=False, comment="Email користувача")
    telegram_id = Column(
        BigInteger, index=True, nullable=True, comment="ID користувача в Telegram"
    )
    telegram_username = Column(
        String(255), nullable=True, comment="Username користувача в Telegram"
    )
    is_used = Column(
        Boolean, default=False, comment="Чи був використаний код автентифікації"
    )
    expires_at = Column(DateTime, nullable=False, comment="Час закінчення терміну дії")
    processed_at = Column(DateTime, nullable=True, comment="Час обробки")

    # Налаштування для універсальних маршрутів
    use_generic_routes = True
    search_fields = ["email", "telegram_username"]
    default_order_by = ["-created_at"]

    @property
    def is_expired(self) -> bool:
        """
        Перевіряє, чи минув термін дії коду.

        Returns:
            bool: True, якщо термін дії минув, інакше False
        """
        timezone = pytz.timezone(settings.TIMEZONE)
        now = datetime.now(timezone)
        return now > self.expires_at

    def generate_deep_link(self) -> str:
        """
        Генерує deep link для Telegram бота.

        Returns:
            str: Deep link для автентифікації через Telegram
        """
        bot_username = settings.TELEGRAM_BOT_USERNAME
        return f"https://t.me/{bot_username}?start=auth_{self.auth_code}"


__all__ = ["TelegramAuth"]
