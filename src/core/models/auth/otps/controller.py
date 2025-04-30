"""
Контролер для модуля автентифікації за допомогою OTP.
"""

from datetime import datetime, timedelta, timezone
from fastapi import BackgroundTasks, HTTPException
from typing import Optional, Dict, Any
import pytz
from sqlalchemy import select

# Add the missing import for database session
from src.core.database.connection import AsyncSessionLocal

from src.core.models.auth.users.controller import UserController
from src.core.models.auth.users.schemas import UserCreate
from src.core.models.auth.roles.controller import role_controller
from src.core.schemas.responses import Success, Fail


from src.config.settings import settings
from src.core.models.logging.providers import get_global_logger

from src.core.models.auth.otps.model import OTP
from src.core.models.auth.otps.schemas import (
    CredentialsSchema,
    JWTPayload,
    RequestOTPSchema,
    VerifyOTPSchema,
)
from src.core.models.auth.otps.service import create_access_token, create_otp, verify_otp

# Отримуємо логер
logger = get_global_logger()


class OTPController:
    """Контролер для управління OTP автентифікацією."""

    def __init__(self):
        # Отримуємо екземпляр UserController
        self.user_controller = UserController()

    async def log_action(self, log_type, log_detail_type, by_user_id=0):
        """Логування дій користувача"""
        logger.info(
            f"User action: {log_detail_type}",
            module="auth.otp",
            data={"log_type": log_type, "by_user_id": by_user_id},
        )

    async def create_otp_record(
        self, email: str, code: str, expires_at: Optional[datetime] = None
    ) -> OTP:
        """
        Створює новий OTP запис з даними користувача.

        Args:
            email: Електронна пошта користувача
            code: Код OTP
            expires_at: Час закінчення терміну дії (за замовчуванням - поточний час + EXPIRY_MINUTES)

        Returns:
            OTP: Новий екземпляр OTP
        """
        # Використовуємо налаштування для часу закінчення терміну дії OTP, якщо не передано явно
        if expires_at is None:
            timezone = pytz.timezone(settings.TIMEZONE)
            now = datetime.now(timezone)
            expires_at = now + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)

        # Створюємо новий екземпляр OTP
        otp = OTP(email=email, code=code, expires_at=expires_at, processed_at=None)

        # Зберігаємо OTP в базі даних через SQLAlchemy
        async with AsyncSessionLocal() as session:
            session.add(otp)
            await session.commit()
            await session.refresh(otp)

        return otp

    async def find_valid_otp(self, email: str, code: str) -> Optional[OTP]:
        """
        Знаходить дійсний OTP для вказаної електронної пошти і коду.

        Args:
            email: Електронна пошта користувача
            code: Код OTP

        Returns:
            OTP: Екземпляр OTP, якщо знайдено, інакше None
        """
        query = (
            select(OTP)
            .where(OTP.email == email)
            .where(OTP.code == code)
            .where(OTP.is_used == False)
            .order_by(OTP.created_at.desc())
        )

        # Виконання запиту через сесію
        async with AsyncSessionLocal() as session:
            result = await session.execute(query)
            otp = result.scalars().first()

            if otp and not otp.is_expired:
                return otp

        return None

    async def login_token(self, username: str, password: str) -> Dict[str, Any]:
        """Аутентифікація користувача за логіном та паролем."""
        if not settings.ENABLE_PASSWORD_AUTH:
            raise HTTPException(
                status_code=404, detail="Password authentication is disabled"
            )

        logger.debug(f"Token request received for user: {username}")
        # Виправлено: передаємо username та password як окремі параметри у метод authenticate
        user_obj = await self.user_controller.authenticate(username, password)

        if not user_obj:
            logger.warning(f"Authentication failed for user: {username}")
            return Fail(code="4010", msg="Invalid credentials")

        await self.log_action(
            log_type="UserLog",
            log_detail_type="UserLoginSuccess",
            by_user_id=user_obj.id,
        )

        payload = JWTPayload(
            data={
                "userId": user_obj.id,
                "userName": user_obj.username,
                "tokenType": "accessToken",
            },
            iat=datetime.now(timezone.utc),
            exp=datetime.now(timezone.utc)
            + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        access_token = create_access_token(data=payload)

        logger.info(f"Successful login for user: {username}")
        return {"access_token": access_token, "token_type": "bearer"}

    async def request_otp(
        self, data: RequestOTPSchema, background_tasks: Optional[BackgroundTasks] = None
    ) -> Dict[str, Any]:
        """Запит OTP для реєстрації або входу."""
        if not settings.ENABLE_OTP_AUTH:
            raise HTTPException(
                status_code=404, detail="OTP authentication is disabled"
            )

        existing_user = await self.user_controller.get_by_email(data.email)

        try:
            await create_otp(data.email, background_tasks)
            return Success(
                msg="OTP sent successfully", data={"isNewUser": existing_user is None}
            )
        except Exception as e:
            logger.error(f"Error sending OTP: {str(e)}")
            return Fail(code="5000", msg="Error sending OTP")

    async def verify_otp_register(self, data: VerifyOTPSchema) -> Dict[str, Any]:
        """Перевірка OTP для реєстрації."""
        if not settings.ENABLE_OTP_AUTH:
            raise HTTPException(
                status_code=404, detail="OTP authentication is disabled"
            )

        existing_user = await self.user_controller.get_by_email(data.email)
        if existing_user:
            return Fail(code="4000", msg="User with this email already exists")

        # Перевірка OTP
        is_valid = await verify_otp(data.email, data.otp)
        if not is_valid:
            return Fail(code="4000", msg="Invalid or expired OTP")

        try:
            # Отримуємо роль користувача за назвою
            role = await role_controller.get_by_name("user")

            # Створюємо користувача
            user_data = UserCreate(
                username=data.email,
                email=data.email,
                first_name=data.email.split("@")[0],
                password=data.otp,  # Використовуємо OTP як початковий пароль
            )
            user = await self.user_controller.create(user_data)

            # Додаємо роль користувачу, якщо вона існує
            if role:
                await self.user_controller.assign_role(user.id, role.id)

            # Створюємо токен для користувача
            payload = JWTPayload(
                data={
                    "userId": user.id,
                    "userName": user.username,
                    "tokenType": "accessToken",
                },
                iat=datetime.now(timezone.utc),
                exp=datetime.now(timezone.utc)
                + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
            )
            access_token = create_access_token(data=payload)

            # Повертаємо дані користувача і токен
            return Success(
                data={
                    "userId": user.id,
                    "userName": user.username,
                    "token": access_token,
                }
            )

        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return Fail(code="5000", msg="Error creating user")

    async def login_with_otp(self, email: str, otp: str) -> Dict[str, Any]:
        """Аутентифікація користувача за допомогою OTP."""
        if not settings.ENABLE_OTP_AUTH:
            raise HTTPException(
                status_code=404, detail="OTP authentication is disabled"
            )

        # Перевіряємо OTP
        is_valid = await verify_otp(email, otp)
        if not is_valid:
            return Fail(code="4000", msg="Invalid or expired OTP")

        # Отримуємо користувача і створюємо токен
        user = await self.user_controller.get_by_email(email)
        if not user:
            return Fail(code="4040", msg="User not found")

        payload = JWTPayload(
            data={
                "userId": user.id,
                "userName": user.username,
                "tokenType": "accessToken",
            },
            iat=datetime.now(timezone.utc),
            exp=datetime.now(timezone.utc)
            + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        access_token = create_access_token(data=payload)

        return Success(
            data={"userId": user.id, "userName": user.username, "token": access_token}
        )

    async def check_email(self, email: str) -> Dict[str, Any]:
        """Перевірка наявності email у системі."""
        existing_user = await self.user_controller.get_by_email(email)
        return Success(data={"exists": existing_user is not None})


# Створюємо екземпляр контролера для глобального використання
otp_controller = OTPController()
