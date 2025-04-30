"""
Сервіс для автентифікації через Telegram.
"""

import uuid
import pytz
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

from sqlalchemy import select

from src.core.database.connection import AsyncSessionLocal
from src.config.settings import settings
from src.core.models.logging.providers import get_global_logger
from src.core.exceptions.exceptions import HTTPException

# Імпорт моделі TelegramAuth
from .model import TelegramAuth

# Отримуємо логер
logger = get_global_logger()


def generate_auth_code() -> str:
    """
    Генерує унікальний код автентифікації для Telegram.

    Returns:
        str: Унікальний код автентифікації
    """
    # Генеруємо випадковий токен довжиною 32 символи
    return secrets.token_urlsafe(32)


async def create_telegram_auth(
    email: str, expires_minutes: int = 15
) -> Tuple[TelegramAuth, str]:
    """
    Створює новий запис автентифікації через Telegram.

    Args:
        email: Email користувача
        expires_minutes: Час дії коду в хвилинах

    Returns:
        Tuple[TelegramAuth, str]: Екземпляр TelegramAuth і deep link для Telegram
    """
    # Генеруємо унікальний код
    auth_code = generate_auth_code()

    # Визначаємо час закінчення терміну дії
    timezone = pytz.timezone(settings.TIMEZONE)
    now = datetime.now(timezone)
    expires_at = now + timedelta(minutes=expires_minutes)

    # Створюємо запис у базі даних
    telegram_auth = TelegramAuth(
        auth_code=auth_code,
        email=email,
        expires_at=expires_at,
    )

    async with AsyncSessionLocal() as session:
        session.add(telegram_auth)
        await session.commit()
        await session.refresh(telegram_auth)

    # Генеруємо deep link для Telegram бота
    deep_link = telegram_auth.generate_deep_link()

    logger.info(f"Created Telegram authentication for {email}", module="auth.telegram")

    return telegram_auth, deep_link


async def verify_telegram_auth(
    auth_code: str, email: Optional[str] = None
) -> Optional[TelegramAuth]:
    """
    Перевіряє код автентифікації Telegram.

    Args:
        auth_code: Код автентифікації
        email: Email користувача для додаткової перевірки (опціонально)

    Returns:
        Optional[TelegramAuth]: Екземпляр TelegramAuth, якщо код дійсний, інакше None
    """
    query = (
        select(TelegramAuth)
        .where(TelegramAuth.auth_code == auth_code)
        .where(TelegramAuth.is_used == False)
    )

    # Якщо вказано email, додаємо його до умов пошуку
    if email:
        query = query.where(TelegramAuth.email == email)

    async with AsyncSessionLocal() as session:
        result = await session.execute(query)
        telegram_auth = result.scalars().first()

        if not telegram_auth:
            logger.warning(
                f"Telegram auth code not found: {auth_code}", module="auth.telegram"
            )
            return None

        # Перевіряємо термін дії
        if telegram_auth.is_expired:
            logger.warning(
                f"Telegram auth code expired: {auth_code}", module="auth.telegram"
            )
            return None

        return telegram_auth


async def process_telegram_callback(
    auth_code: str, telegram_id: int, telegram_username: Optional[str] = None
) -> Optional[TelegramAuth]:
    """
    Обробляє колбек від Telegram бота і оновлює запис автентифікації.

    Args:
        auth_code: Код автентифікації
        telegram_id: ID користувача в Telegram
        telegram_username: Username користувача в Telegram

    Returns:
        Optional[TelegramAuth]: Оновлений екземпляр TelegramAuth або None
    """
    # Перевіряємо код автентифікації
    telegram_auth = await verify_telegram_auth(auth_code)

    if not telegram_auth:
        return None

    # Оновлюємо запис з інформацією з Telegram
    async with AsyncSessionLocal() as session:
        telegram_auth.telegram_id = telegram_id
        telegram_auth.telegram_username = telegram_username

        session.add(telegram_auth)
        await session.commit()
        await session.refresh(telegram_auth)

        logger.info(
            f"Updated Telegram auth with user data: {telegram_id}",
            module="auth.telegram",
        )

        return telegram_auth


async def complete_telegram_auth(auth_code: str) -> Optional[TelegramAuth]:
    """
    Завершує процес автентифікації через Telegram, позначаючи код як використаний.

    Args:
        auth_code: Код автентифікації

    Returns:
        Optional[TelegramAuth]: Оновлений екземпляр TelegramAuth або None
    """
    # Перевіряємо код автентифікації
    telegram_auth = await verify_telegram_auth(auth_code)

    if not telegram_auth:
        return None

    # Перевіряємо, чи прив'язано Telegram ID
    if not telegram_auth.telegram_id:
        logger.warning(
            f"Telegram auth not completed: no Telegram ID for code {auth_code}",
            module="auth.telegram",
        )
        return None

    # Позначаємо код як використаний
    async with AsyncSessionLocal() as session:
        telegram_auth.is_used = True
        telegram_auth.processed_at = datetime.now()

        session.add(telegram_auth)
        await session.commit()
        await session.refresh(telegram_auth)

        logger.info(
            f"Completed Telegram auth for user {telegram_auth.email}",
            module="auth.telegram",
        )

        return telegram_auth


async def find_user_by_telegram_id(telegram_id: int) -> Optional[Dict[str, Any]]:
    """
    Знаходить користувача за Telegram ID на основі історії автентифікацій.

    Args:
        telegram_id: ID користувача в Telegram

    Returns:
        Optional[Dict[str, Any]]: Інформація про останню успішну автентифікацію
    """
    query = (
        select(TelegramAuth)
        .where(TelegramAuth.telegram_id == telegram_id)
        .where(TelegramAuth.is_used == True)
        .order_by(TelegramAuth.processed_at.desc())
    )

    async with AsyncSessionLocal() as session:
        result = await session.execute(query)
        telegram_auth = result.scalars().first()

        if not telegram_auth:
            return None

        return {
            "email": telegram_auth.email,
            "telegram_id": telegram_auth.telegram_id,
            "telegram_username": telegram_auth.telegram_username,
            "last_auth": telegram_auth.processed_at,
        }


async def cleanup_expired_auth_codes() -> int:
    """
    Очищує застарілі коди автентифікації.

    Returns:
        int: Кількість видалених записів
    """
    timezone = pytz.timezone(settings.TIMEZONE)
    now = datetime.now(timezone)

    async with AsyncSessionLocal() as session:
        # Знаходимо всі застарілі невикористані коди
        query = (
            select(TelegramAuth)
            .where(TelegramAuth.expires_at < now)
            .where(TelegramAuth.is_used == False)
        )

        result = await session.execute(query)
        expired_auths = result.scalars().all()

        # Видаляємо їх
        count = 0
        for auth in expired_auths:
            await session.delete(auth)
            count += 1

        await session.commit()

        logger.info(
            f"Cleaned up {count} expired Telegram auth codes", module="auth.telegram"
        )
        return count
