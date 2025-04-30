"""
Сервіс для роботи з OTP - видача, перевірка, управління.
"""

from pathlib import Path
import random
from fastapi_mail import MessageSchema
from jinja2 import Template
import pytz
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi_mail.errors import ConnectionErrors

from src.core.database.connection import AsyncSessionLocal
from src.config.settings import settings
from src.core.models.logging.providers import get_global_logger
from src.core.exceptions.exceptions import HTTPException

# Імпорт моделі OTP (але не контролера!)
from .model import OTP

# Отримуємо логер
logger = get_global_logger()


def generate_otp() -> str:
    """
    Згенерувати 6-значний OTP код.

    Returns:
        str: 6-значний OTP код
    """
    return "".join([str(random.randint(0, 9)) for _ in range(6)])


async def create_otp_record(
    email: str, code: str, expires_at: Optional[datetime] = None
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


async def find_valid_otp(email: str, code: str) -> Optional[OTP]:
    """
    Знаходить дійсний OTP для вказаної електронної пошти і коду.

    Args:
        email: Електронна пошта користувача
        code: Код OTP

    Returns:
        Optional[OTP]: Екземпляр OTP, якщо знайдено, інакше None
    """
    from sqlalchemy import select

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


async def create_otp(
    email: str, background_tasks: Optional[BackgroundTasks] = None
) -> Dict[str, Any]:
    """
    Створює OTP для вказаної електронної пошти та надсилає його поштою.

    Args:
        email: Електронна пошта користувача
        background_tasks: Завдання у фоні для відправки електронної пошти

    Returns:
        Dict[str, Any]: Результат операції
    """
    # Перевіряємо, чи увімкнена OTP автентифікація
    if not settings.ENABLE_OTP_AUTH:
        logger.error("OTP authentication is disabled in settings")
        raise HTTPException(status_code=404, detail="OTP authentication is disabled")

    try:
        # Генеруємо OTP код
        code = generate_otp()

        # Створюємо запис OTP
        otp = await create_otp_record(email, code)

        # Відправляємо електронною поштою, якщо доступно
        if settings.ENABLE_EMAIL_NOTIFICATIONS:
            # Якщо відправка електронної пошти налаштована
            await send_otp_email(email, code, background_tasks)

        logger.info(f"Created OTP for {email}", module="auth.otp")
        return {"success": True, "message": "OTP created and sent"}

    except Exception as e:
        logger.error(f"Error creating OTP: {str(e)}", module="auth.otp")
        return {"success": False, "error": str(e)}


async def verify_otp(email: str, code: str) -> bool:
    """
    Перевіряє OTP та позначає його як використаний, якщо він дійсний.

    Args:
        email: Електронна пошта користувача
        code: Код OTP

    Returns:
        bool: True, якщо OTP дійсний і був успішно використаний, інакше False
    """
    # Перевіряємо, чи увімкнена OTP автентифікація
    if not settings.ENABLE_OTP_AUTH:
        logger.error("OTP authentication is disabled in settings")
        return False

    try:
        # Шукаємо дійсний OTP
        otp = await find_valid_otp(email, code)

        if not otp:
            logger.warning(f"Invalid or expired OTP for {email}")
            return False

        # Позначаємо OTP як використаний
        async with AsyncSessionLocal() as session:
            otp.is_used = True
            otp.processed_at = datetime.now()
            session.add(otp)
            await session.commit()

        logger.info(f"OTP verified for {email}")
        return True

    except Exception as e:
        logger.error(f"Error verifying OTP: {str(e)}")
        return False


def create_access_token(data) -> str:
    """
    Створює JWT токен доступу.

    Args:
        data: JWT payload

    Returns:
        str: JWT токен
    """
    import jwt

    token = jwt.encode(
        payload=data.dict(),
        key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return token

async def load_template(template_name: str, context: dict) -> str:
    template_path = Path(settings.PROJECT_ROOT) / 'templates' / 'email' / template_name
    with open(template_path, 'r', encoding='utf-8') as file:
        template = Template(file.read())
    return template.render(context)

async def send_otp_email(email: str, otp: str, background_tasks: BackgroundTasks):
    """Send OTP via email"""
    try:
        body = await load_template('otp_template.html', {'otp': otp})

        message = MessageSchema(
            subject="Your OTP Code",
            recipients=[email],
            body=body,
            subtype="html"
        )

        background_tasks.add_task(FastMail.send_message, message)
        logger.info(f"OTP email sent successfully to {email}")
        return True

    except ConnectionError as e:
        logger.error(f"Failed to send email to {email} due to connection error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Failed to send email to {email}: {str(e)}")
        return False
