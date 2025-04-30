"""
Контролер для роботи з автентифікацією через Telegram.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

from fastapi import HTTPException

from src.core.models.auth.users.controller import UserController
from src.core.models.auth.users.schemas import UserCreate
from src.core.models.auth.roles.controller import role_controller
from src.core.schemas.responses import Success, Fail

from src.config.settings import settings
from src.core.models.logging.providers import get_global_logger

# Імпорти для роботи з Telegram Auth
from .model import TelegramAuth
from .schemas import (
    RequestTelegramAuthSchema,
    VerifyTelegramAuthSchema,
    TelegramCallbackSchema,
)
from .service import (
    create_telegram_auth,
    verify_telegram_auth,
    process_telegram_callback,
    complete_telegram_auth,
    find_user_by_telegram_id,
)

# Функція для створення JWT токена
from src.core.models.auth.otps.schemas import JWTPayload
from src.core.models.auth.otps.service import create_access_token

# Отримуємо логер
logger = get_global_logger()


class TelegramAuthController:
    """Контролер для управління автентифікацією через Telegram."""

    def __init__(self):
        # Отримуємо екземпляр UserController для роботи з користувачами
        self.user_controller = UserController()

    async def log_action(
        self, log_type: str, log_detail_type: str, by_user_id: str = "0"
    ) -> None:
        """Логування дій користувача"""
        logger.info(
            f"User action: {log_detail_type}",
            module="auth.telegram",
            data={"log_type": log_type, "by_user_id": by_user_id},
        )

    async def request_auth_link(
        self, data: RequestTelegramAuthSchema
    ) -> Dict[str, Any]:
        """
        Створює посилання для автентифікації через Telegram.

        Args:
            data: Дані запиту з email користувача

        Returns:
            Dict[str, Any]: Результат операції з посиланням або помилкою
        """
        # Перевіряємо, чи включена автентифікація через Telegram
        if not settings.ENABLE_TELEGRAM_AUTH:
            logger.warning("Telegram authentication is disabled")
            return Fail(code="4040", msg="Telegram authentication is disabled")

        try:
            # Перевіряємо, чи існує користувач з таким email
            user = await self.user_controller.get_by_email(data.email)

            # Створюємо запис і отримуємо deep link
            telegram_auth, deep_link = await create_telegram_auth(
                data.email, expires_minutes=settings.TELEGRAM_AUTH_EXPIRY_MINUTES
            )

            # Обчислюємо час до закінчення терміну дії в секундах
            expires_in = int(
                (telegram_auth.expires_at - datetime.now(timezone.utc)).total_seconds()
            )

            # Повертаємо успішний результат
            return Success(
                msg="Authentication link created",
                data={
                    "auth_link": deep_link,
                    "expires_in": expires_in,
                    "email": data.email,
                    "is_new_user": user is None,
                },
            )

        except Exception as e:
            logger.error(f"Error creating Telegram auth link: {str(e)}")
            return Fail(code="5000", msg="Failed to create authentication link")

    async def process_bot_callback(
        self, data: TelegramCallbackSchema
    ) -> Dict[str, Any]:
        """
        Обробляє callback від Telegram бота.

        Args:
            data: Дані від Telegram бота

        Returns:
            Dict[str, Any]: Результат обробки
        """
        try:
            # Обробляємо callback і оновлюємо запис
            telegram_auth = await process_telegram_callback(
                data.auth_code, data.telegram_id, data.telegram_username
            )

            if not telegram_auth:
                return Fail(code="4040", msg="Invalid or expired authentication code")

            # Повертаємо успішний результат
            return Success(
                msg="Telegram authentication confirmed",
                data={
                    "email": telegram_auth.email,
                    "telegram_id": telegram_auth.telegram_id,
                    "telegram_username": telegram_auth.telegram_username,
                },
            )

        except Exception as e:
            logger.error(f"Error processing Telegram callback: {str(e)}")
            return Fail(code="5000", msg="Failed to process Telegram authentication")

    async def verify_and_login(self, data: VerifyTelegramAuthSchema) -> Dict[str, Any]:
        """
        Перевіряє код автентифікації та виконує вхід або реєстрацію.

        Args:
            data: Дані для перевірки коду автентифікації

        Returns:
            Dict[str, Any]: Результат автентифікації з токеном доступу
        """
        # Перевіряємо, чи включена автентифікація через Telegram
        if not settings.ENABLE_TELEGRAM_AUTH:
            logger.warning("Telegram authentication is disabled")
            return Fail(code="4040", msg="Telegram authentication is disabled")

        try:
            # Перевіряємо код автентифікації
            telegram_auth = await verify_telegram_auth(data.auth_code, data.email)

            if not telegram_auth:
                return Fail(code="4000", msg="Invalid or expired authentication code")

            # Перевіряємо, чи прив'язано Telegram ID
            if not telegram_auth.telegram_id:
                return Fail(code="4000", msg="Authentication not confirmed in Telegram")

            # Шукаємо користувача за email
            user = await self.user_controller.get_by_email(telegram_auth.email)

            # Якщо користувача не існує, створюємо нового
            if not user:
                # Отримуємо роль користувача за назвою
                role = await role_controller.get_by_name("user")

                # Створюємо пароль (можна використовувати Telegram ID як частину пароля)
                import secrets

                password = secrets.token_urlsafe(16)

                # Створюємо користувача
                user_data = UserCreate(
                    username=telegram_auth.email,
                    email=telegram_auth.email,
                    first_name=telegram_auth.email.split("@")[0],
                    password=password,
                )
                user = await self.user_controller.create(user_data)

                # Додаємо роль користувачу, якщо вона існує
                if role:
                    await self.user_controller.assign_role(user.id, role.id)

                # Зберігаємо Telegram ID і username
                await self.user_controller.update_telegram_info(
                    user.id, telegram_auth.telegram_id, telegram_auth.telegram_username
                )

                logger.info(f"Created new user via Telegram auth: {user.email}")

            # Оновлюємо запис автентифікації
            await complete_telegram_auth(data.auth_code)

            # Оновлюємо дату останнього входу
            await self.user_controller.update_last_login(user.id)

            # Створюємо JWT токен
            payload = JWTPayload(
                data={
                    "userId": user.id,
                    "userName": user.username,
                    "tokenType": "accessToken",
                    "telegramId": str(telegram_auth.telegram_id),
                },
                iat=datetime.now(timezone.utc),
                exp=datetime.now(timezone.utc)
                + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
            )

            access_token = create_access_token(data=payload)

            # Логуємо успішний вхід
            await self.log_action(
                log_type="UserLog",
                log_detail_type="TelegramLoginSuccess",
                by_user_id=user.id,
            )

            # Повертаємо успішний результат
            return Success(
                msg="Authentication successful",
                data={
                    "userId": user.id,
                    "userName": user.username,
                    "email": user.email,
                    "token": access_token,
                },
            )

        except Exception as e:
            logger.error(f"Error in Telegram authentication: {str(e)}")
            return Fail(code="5000", msg="Failed to authenticate")

    async def login_by_telegram_id(self, telegram_id: int) -> Dict[str, Any]:
        """
        Виконує вхід за допомогою Telegram ID (для використання в боті).

        Args:
            telegram_id: ID користувача в Telegram

        Returns:
            Dict[str, Any]: Результат автентифікації
        """
        try:
            # Шукаємо користувача по Telegram ID
            user_info = await find_user_by_telegram_id(telegram_id)

            if not user_info:
                return Fail(code="4040", msg="User not found for this Telegram ID")

            # Шукаємо користувача за email
            user = await self.user_controller.get_by_email(user_info["email"])

            if not user:
                return Fail(code="4040", msg="User account not found")

            # Оновлюємо дату останнього входу
            await self.user_controller.update_last_login(user.id)

            # Створюємо JWT токен
            payload = JWTPayload(
                data={
                    "userId": user.id,
                    "userName": user.username,
                    "tokenType": "accessToken",
                    "telegramId": str(telegram_id),
                },
                iat=datetime.now(timezone.utc),
                exp=datetime.now(timezone.utc)
                + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
            )

            access_token = create_access_token(data=payload)

            # Логуємо успішний вхід
            await self.log_action(
                log_type="UserLog",
                log_detail_type="TelegramDirectLoginSuccess",
                by_user_id=user.id,
            )

            # Повертаємо успішний результат
            return Success(
                msg="Direct Telegram login successful",
                data={
                    "userId": user.id,
                    "userName": user.username,
                    "email": user.email,
                    "token": access_token,
                },
            )

        except Exception as e:
            logger.error(f"Error in direct Telegram login: {str(e)}")
            return Fail(code="5000", msg="Failed to authenticate via Telegram")


# Створюємо екземпляр контролера для глобального використання
telegram_auth_controller = TelegramAuthController()
