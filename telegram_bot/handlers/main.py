"""
Головний файл для керування всіма обробниками
"""

from telegram_bot.handlers.user.basic import register_user_handlers
from telegram_bot.handlers.common.dispatcher import button_handlers


# Старі імпорти для сумісності
from telegram_bot.handlers.common.balance import *
from telegram_bot.handlers.common.history import *
from telegram_bot.handlers.common.admin import *
from telegram_bot.handlers.common.bonus import *
from telegram_bot.handlers.common.share_phone import *


def register_all_handlers(dp, menu_manager=None):
    """Реєстрація всіх обробників"""
    import logging

    logger = logging.getLogger("telegram_bot.handlers")

    # Основні обробники користувача
    register_user_handlers(dp, menu_manager)

    # Реєструємо команди для роботи з бонусами
    from telegram_bot.handlers.commands.bonus_commands import register_bonus_commands

    register_bonus_commands(dp)

    # Логування зареєстрованих button handlers
    logger.info(f"Зареєстровано button handlers: {list(button_handlers.keys())}")

    # Реєстрація button handlers з navigation system
    from telegram_bot.navigation.decorators import get_button_handlers

    for handler_name, handler_func in get_button_handlers().items():
        if menu_manager:
            menu_manager.register_button_handler(handler_name, handler_func)

    logger.info("Всі handlers зареєстровано успішно")


def register_handlers(dp):
    """Стара функція для сумісності"""
    # Реєстрація хендлерів для кнопок
    from aiogram import F
    from aiogram.types import Message

    async def button_router(message: Message):
        # Try using the navigation system first
        menu_manager = dp.get("menu_manager")
        if menu_manager:
            handled = await menu_manager.handle_button(message)
            if handled:
                return

        # Fallback to old handler system
        handler_name = message.text.strip()
        if handler_name in button_handlers:
            try:
                await button_handlers[handler_name](message)
            except Exception as e:
                import logging

                logger = logging.getLogger("telegram_bot")
                logger.error(f"Error in button handler {handler_name}: {e}")

    # Register the button router
    dp.message.register(button_router, F.text)
