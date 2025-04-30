"""
Маршрути API для автентифікації через Telegram.
"""

from fastapi import APIRouter, Depends, Body

# Імпорти для автоматичної генерації API
from src.core.loader_factory.api_factory.routes import create_api_router
from src.core.loader_factory.api_factory.controller import create_controller
from src.core.security.jwt import require_auth, get_current_admin_user

# Імпорти для Telegram Auth
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

# Створюємо маршрутизатор для публічних API ендпоінтів
router = APIRouter(
    tags=["auth", "telegram"],
    responses={404: {"description": "Not found"}},
)


# Ендпоінт для запиту посилання на автентифікацію через Telegram
@router.post("/request-link")
async def request_telegram_auth_link(data: RequestTelegramAuthSchema = Body(...)):
    """
    Створює посилання для автентифікації через Telegram.

    Повертає deep link, який слід відкрити для початку процесу автентифікації через Telegram бота.
    """
    return await telegram_auth_controller.request_auth_link(data)


# Ендпоінт для перевірки коду автентифікації та входу в систему
@router.post("/verify")
async def verify_telegram_auth(data: VerifyTelegramAuthSchema = Body(...)):
    """
    Перевіряє код автентифікації Telegram і виконує вхід або реєстрацію.

    Якщо код автентифікації дійсний і підтверджений в Telegram, створює сесію користувача.
    """
    return await telegram_auth_controller.verify_and_login(data)


# Ендпоінт для обробки callback від Telegram бота
@router.post("/callback")
async def process_telegram_callback(data: TelegramCallbackSchema = Body(...)):
    """
    Обробляє callback від Telegram бота.

    Цей ендпоінт призначений для використання Telegram ботом для підтвердження автентифікації.
    """
    return await telegram_auth_controller.process_bot_callback(data)


# Ендпоінт для прямого входу за Telegram ID (для використання в боті)
@router.post("/direct-login/{telegram_id}")
async def direct_telegram_login(telegram_id: int):
    """
    Виконує пряму автентифікацію за Telegram ID.

    Цей ендпоінт призначений для використання всередині Telegram бота,
    щоб користувачі могли входити напряму з бота без додаткових підтверджень.
    """
    return await telegram_auth_controller.login_by_telegram_id(telegram_id)


# Створюємо додатковий маршрутизатор для адміністративних API ендпоінтів
admin_router = create_api_router(
    controller=create_controller(TelegramAuth, TelegramAuthResponse),
    create_schema=TelegramAuthCreate,
    update_schema=TelegramAuthUpdate,
    response_schema=TelegramAuthResponse,
    prefix="/admin",
    tags=["auth", "telegram", "admin"],
    auth_dependency=require_auth,
    admin_dependency=get_current_admin_user,
    include_public_routes=False,  # Відключаємо публічний доступ
    include_protected_routes=False,  # Відключаємо захищений доступ
    include_admin_routes=True,  # Включаємо тільки адміністративний доступ
)

# Додаємо адміністративний маршрутизатор до основного
router.include_router(admin_router)
