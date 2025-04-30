"""
Модуль для реалізації Telegram бота для автентифікації.

Цей файл містить основну логіку для Telegram бота, який
обробляє посилання для автентифікації та надсилає підтвердження
до API.
"""

import logging
import asyncio
import httpx
from typing import Dict, Any, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from src.config.settings import settings
from src.core.models.logging.providers import get_global_logger

# Отримуємо логер
logger = get_global_logger()
if not logger:
    logger = logging.getLogger(__name__)

# URL для відправки callback API
API_URL = f"{settings.API_BASE_URL}/api/v1/telegram/callback"
API_DIRECT_LOGIN_URL = f"{settings.API_BASE_URL}/api/v1/telegram/direct-login"

# Тексти для бота
WELCOME_MESSAGE = (
    "Вітаю! Я бот для автентифікації у системі {app_name}.\n\n"
    "Для входу в систему перейдіть на сайт і виберіть 'Увійти через Telegram'. "
    "Потім перейдіть за посиланням, яке вам буде надано."
)

AUTH_REQUEST_MESSAGE = (
    "🔐 Запит на автентифікацію для {email}.\n\n"
    "Якщо це ви намагаєтеся увійти в систему {app_name}, натисніть кнопку 'Підтвердити'.\n\n"
    "Якщо ви не намагаєтеся увійти, проігноруйте це повідомлення."
)

AUTH_CONFIRMED_MESSAGE = (
    "✅ Автентифікацію підтверджено!\n\n"
    "Ви можете повернутися на сайт {app_name} і продовжити роботу."
)

AUTH_ERROR_MESSAGE = (
    "❌ Помилка підтвердження автентифікації.\n\n"
    "Будь ласка, спробуйте знову або зверніться до служби підтримки."
)

DIRECT_LOGIN_MESSAGE = (
    "🔑 Ви вже авторизовані через Telegram!\n\n"
    "Для швидкого входу в систему {app_name} просто натисніть кнопку нижче."
)


async def send_callback_to_api(
    auth_code: str, user_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Відправляє callback до API для підтвердження автентифікації.
    
    Args:
        auth_code: Код автентифікації
        user_data: Дані користувача з Telegram
        
    Returns:
        Optional[Dict[str, Any]]: Відповідь API або None у разі помилки
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                API_URL,
                json={
                    "auth_code": auth_code,
                    "telegram_id": user_data["id"],
                    "telegram_username": user_data.get("username"),
                    "first_name": user_data.get("first_name"),
                    "last_name": user_data.get("last_name"),
                },
                headers={"Content-Type": "application/json"},
                timeout=10.0,
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"API error: {response.status_code} - {response.text}",
                    module="auth.telegram.bot",
                )
                return None
    
    except Exception as e:
        logger.error(
            f"Error sending callback to API: {str(e)}",
            module="auth.telegram.bot",
        )
        return None


async def direct_login(telegram_id: int) -> Optional[Dict[str, Any]]:
    """
    Виконує прямий вхід через Telegram ID.
    
    Args:
        telegram_id: ID користувача в Telegram
        
    Returns:
        Optional[Dict[str, Any]]: Відповідь API або None у разі помилки
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_DIRECT_LOGIN_URL}/{telegram_id}",
                headers={"Content-Type": "application/json"},
                timeout=10.0,
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"API direct login error: {response.status_code} - {response.text}",
                    module="auth.telegram.bot",
                )
                return None
    
    except Exception as e:
        logger.error(
            f"Error in direct login: {str(e)}",
            module="auth.telegram.bot",
        )
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обробляє команду /start і перевіряє наявність коду автентифікації.
    """
    user = update.effective_user
    args = context.args
    
    # Перевіряємо, чи є аргументи
    if not args:
        # Звичайний старт без коду автентифікації
        await update.message.reply_text(
            WELCOME_MESSAGE.format(app_name=settings.APP_NAME)
        )
        
        # Перевіряємо, чи зареєстрований користувач в системі
        result = await direct_login(user.id)
        
        if result and result.get("status") == "success":
            # Пропонуємо швидкий вхід
            keyboard = [
                [
                    InlineKeyboardButton(
                        f"Увійти в {settings.APP_NAME}", 
                        url=f"{settings.WEBSITE_URL}?telegramLogin={user.id}"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                DIRECT_LOGIN_MESSAGE.format(app_name=settings.APP_NAME),
                reply_markup=reply_markup,
            )
        
        return
    
    # Обробка коду автентифікації
    arg = args[0]
    
    # Перевіряємо, чи це код автентифікації
    if arg.startswith("auth_"):
        auth_code = arg[5:]  # Видаляємо префікс "auth_"
        
        # Зберігаємо в контексті для використання в колбеках
        context.user_data["auth_code"] = auth_code
        
        # Отримуємо інформацію про запит автентифікації з API
        result = await send_callback_to_api(auth_code, user.to_dict())
        
        if result and result.get("status") == "success":
            # Отримуємо email з відповіді
            email = result.get("data", {}).get("email", "користувача")
            
            # Створюємо клавіатуру з кнопкою підтвердження
            keyboard = [
                [InlineKeyboardButton("Підтвердити", callback_data=f"confirm_{auth_code}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                AUTH_REQUEST_MESSAGE.format(email=email, app_name=settings.APP_NAME),
                reply_markup=reply_markup,
            )
        else:
            await update.message.reply_text(AUTH_ERROR_MESSAGE)
    else:
        # Невідомий аргумент
        await update.message.reply_text(
            WELCOME_MESSAGE.format(app_name=settings.APP_NAME)
        )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обробляє натискання кнопок в інлайн-клавіатурі.
    """
    query = update.callback_query
    await query.answer()
    
    # Обробляємо різні типи колбеків
    if query.data.startswith("confirm_"):
        auth_code = query.data[8:]  # Видаляємо префікс "confirm_"
        
        # Відправляємо підтвердження до API
        result = await send_callback_to_api(auth_code, query.from_user.to_dict())
        
        if result and result.get("status") == "success":
            await query.edit_message_text(
                AUTH_CONFIRMED_MESSAGE.format(app_name=settings.APP_NAME)
            )
        else:
            await query.edit_message_text(AUTH_ERROR_MESSAGE)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обробляє команду /help.
    """
    await update.message.reply_text(
        f"Цей бот використовується для автентифікації в системі {settings.APP_NAME}.\n\n"
        "Доступні команди:\n"
        "/start - Почати роботу з ботом\n"
        "/help - Показати це повідомлення\n"
        "/login - Швидкий вхід в систему (якщо ви вже зареєстровані)\n\n"
        "Для входу в систему перейдіть на сайт і виберіть 'Увійти через Telegram'."
    )


async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обробляє команду /login.
    """
    user = update.effective_user
    
    # Перевіряємо, чи зареєстрований користувач в системі
    result = await direct_login(user.id)
    
    if result and result.get("status") == "success":
        # Пропонуємо швидкий вхід
        keyboard = [
            [
                InlineKeyboardButton(
                    f"Увійти в {settings.APP_NAME}", 
                    url=f"{settings.WEBSITE_URL}?telegramLogin={user.id}"
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            DIRECT_LOGIN_MESSAGE.format(app_name=settings.APP_NAME),
            reply_markup=reply_markup,
        )
    else:
        await update.message.reply_text(
            "Ви ще не зареєстровані в системі або ваш обліковий запис не пов'язаний з Telegram.\n\n"
            f"Для реєстрації перейдіть на сайт {settings.WEBSITE_URL} і виберіть 'Увійти через Telegram'."
        )


def main() -> None:
    """
    Основна функція для запуску бота.
    """
    # Створюємо екземпляр програми
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Додаємо обробники
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("login", login_command))
    application.add_handler(CallbackQueryHandler(button_callback))

    # Запускаємо бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
