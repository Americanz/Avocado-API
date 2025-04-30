"""
Модуль для автентифікації через Telegram.

Цей модуль забезпечує функціональність автентифікації користувачів
за допомогою Telegram ботів, використовуючи підхід аналогічний OTP,
але з більш зручним користувацьким досвідом.
"""

from .model import TelegramAuth
from .schemas import (
    TelegramAuthCreate,
    TelegramAuthUpdate,
    TelegramAuthResponse,
    RequestTelegramAuthSchema,
    VerifyTelegramAuthSchema,
    TelegramCallbackSchema,
)
from .controller import telegram_auth_controller
from .routes import router

# Експортуємо необхідні компоненти
__all__ = [
    "TelegramAuth",
    "TelegramAuthCreate",
    "TelegramAuthUpdate",
    "TelegramAuthResponse",
    "RequestTelegramAuthSchema",
    "VerifyTelegramAuthSchema",
    "TelegramCallbackSchema",
    "telegram_auth_controller",
    "router",
]
