"""
Модель для зберігання одноразових паролів (OTP).
"""

import pytz

from sqlalchemy import Column, String, Boolean, DateTime
from datetime import datetime

from src.core.models.base_model import BaseModel
from src.config.settings import settings


class OTP(BaseModel):
    """
    Модель для зберігання одноразових паролів (OTP).

    Attributes:
        code: Код OTP (6 цифр)
        email: Email користувача
        is_used: Чи був використаний OTP
        expires_at: Час закінчення терміну дії
        processed_at: Час обробки OTP
    """

    __tablename__ = "otps"

    # Поля моделі (id, created_at, updated_at та is_active наслідуються від BaseModel)
    code = Column(String(6), nullable=False, comment="Код OTP (6 цифр)")
    email = Column(String(255), index=True, nullable=False, comment="Email користувача")
    is_used = Column(Boolean, default=False, comment="Чи був використаний OTP")
    expires_at = Column(DateTime, nullable=False, comment="Час закінчення терміну дії")
    processed_at = Column(DateTime, nullable=True, comment="Час обробки OTP")

    # Налаштування для універсальних маршрутів
    use_generic_routes = True
    search_fields = ["email"]
    default_order_by = ["-created_at"]

    @property
    def is_expired(self) -> bool:
        """
        Перевіряє, чи минув термін дії OTP.

        Returns:
            bool: True, якщо термін дії минув, інакше False
        """
        timezone = pytz.timezone(settings.TIMEZONE)
        now = datetime.now(timezone)
        return now > self.expires_at


__all__ = ["OTP"]
