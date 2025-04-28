"""
Сервісні функції для автентифікації та авторизації.
"""

import jwt
import random
import pytz
from jinja2 import Template
from pathlib import Path
from passlib import pwd
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi_mail.errors import ConnectionErrors
from fastapi import BackgroundTasks

from src.config.settings import settings
from src.core.exceptions.exceptions import HTTPException
from src.core.models.logging.providers import get_global_logger

from .controller import permissions_controller
from .schemas import JWTPayload

# Отримуємо логер
logger = get_global_logger()

# Налаштування хешування паролів
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Налаштування поштового сервера
mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.MAIL_USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
)

fastmail = FastMail(mail_config)


def create_access_token(*, data: JWTPayload) -> str:
    """
    Створити JWT токен доступу.

    Args:
        data: Дані для токена

    Returns:
        Закодований JWT токен
    """
    payload = data.model_dump().copy()
    encoded_jwt = jwt.encode(
        payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Перевірити пароль порівнянням з хешем.

    Args:
        plain_password: Пароль у відкритому вигляді
        hashed_password: Хеш пароля

    Returns:
        True якщо пароль співпадає з хешем, інакше False
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Створити хеш для пароля.

    Args:
        password: Пароль у відкритому вигляді

    Returns:
        Хеш пароля
    """
    return pwd_context.hash(password)


def generate_password() -> str:
    """
    Згенерувати випадковий пароль.

    Returns:
        Випадковий пароль
    """
    return pwd.genword()


def generate_otp() -> str:
    """
    Згенерувати 6-значний OTP код.

    Returns:
        6-значний OTP код
    """
    return "".join([str(random.randint(0, 9)) for _ in range(6)])


async def create_otp(email: str, background_tasks: Optional[BackgroundTasks] = None):
    """
    Створити новий OTP запис з даними користувача та надіслати його поштою.

    Args:
        email: Електронна пошта користувача
        background_tasks: Об'єкт для фонових завдань

    Returns:
        OTP: Створений OTP об'єкт

    Raises:
        HTTPException: Якщо не вдалося створити OTP або надіслати електронний лист
    """
    # Перевіряємо, чи увімкнена OTP авторизація
    if not settings.ENABLE_OTP_AUTH:
        logger.error("OTP authentication is disabled in settings")
        raise HTTPException(code="4040", msg="OTP authentication is disabled")

    code = generate_otp()

    try:
        # Створюємо OTP запис через контролер
        otp = await permissions_controller.create_otp_record(email, code)

        # Надсилаємо OTP по електронній пошті
        success = await send_otp_email(email, code, background_tasks)
        if not success:
            # TODO: Видалити OTP з бази даних, якщо не вдалося відправити лист
            raise HTTPException(code="5000", msg="Failed to send OTP email")

        logger.info(f"OTP created and sent successfully for email: {email}")
        return otp

    except Exception as e:
        # TODO: Видалити OTP з бази даних у разі помилки
        logger.error(f"Error in create_otp: {str(e)}")
        raise HTTPException(code="5000", msg="Failed to process OTP request")


async def verify_otp(email: str, code: str) -> bool:
    """
    Перевірити OTP код.

    Args:
        email: Email користувача
        code: OTP код для перевірки

    Returns:
        True якщо OTP дійсний, інакше False
    """
    # Перевіряємо, чи увімкнена OTP авторизація
    if not settings.ENABLE_OTP_AUTH:
        logger.error("OTP authentication is disabled in settings")
        return False

    try:
        # Знаходимо дійсний OTP через контролер
        otp = await permissions_controller.find_valid_otp(email, code)

        if not otp:
            logger.warning(f"OTP not found or expired for email: {email}")
            return False

        # Позначаємо OTP як використаний
        otp.is_used = True
        otp.processed_at = datetime.now()

        # Зберігаємо зміни в базі даних
        from src.core.database.connection import async_session_maker

        async with async_session_maker() as session:
            session.add(otp)
            await session.commit()

        logger.info(f"OTP verified successfully for email: {email}")
        return True

    except Exception as e:
        logger.error(f"Error in verify_otp: {str(e)}")
        return False


async def load_template(template_name: str, context: dict) -> str:
    """
    Завантажити шаблон електронного листа.

    Args:
        template_name: Назва файлу шаблону
        context: Контекст для шаблону

    Returns:
        Рендерований HTML
    """
    template_path = Path(settings.PROJECT_ROOT) / "templates" / "email" / template_name
    with open(template_path, "r", encoding="utf-8") as file:
        template = Template(file.read())
    return template.render(context)


async def send_otp_email(
    email: str, otp: str, background_tasks: Optional[BackgroundTasks] = None
) -> bool:
    """
    Надіслати OTP по електронній пошті.

    Args:
        email: Email користувача
        otp: OTP код
        background_tasks: Об'єкт для фонових завдань

    Returns:
        True якщо лист успішно надіслано, інакше False
    """
    try:
        body = await load_template("otp_template.html", {"otp": otp})

        message = MessageSchema(
            subject="Your OTP Code", recipients=[email], body=body, subtype="html"
        )

        if background_tasks:
            background_tasks.add_task(fastmail.send_message, message)
        else:
            await fastmail.send_message(message)

        logger.info(f"OTP email sent successfully to {email}")
        return True

    except ConnectionErrors as e:
        logger.error(
            f"Failed to send email to {email} due to connection error: {str(e)}"
        )
        return False
    except Exception as e:
        logger.error(f"Failed to send email to {email}: {str(e)}")
        return False
