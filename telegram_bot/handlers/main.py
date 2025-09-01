"""
Головний файл для керування всіма обробниками
"""

import logging
from aiogram import F
from aiogram.types import Message

from telegram_bot.handlers.user.basic import register_user_handlers
from telegram_bot.handlers.common.dispatcher import button_handlers


def register_all_handlers(dp, menu_manager=None):
    """Реєстрація всіх обробників"""
    logger = logging.getLogger("telegram_bot.handlers")

    # Основні обробники користувача
    register_user_handlers(dp, menu_manager)

    # Реєструємо команди для роботи з бонусами
    from telegram_bot.handlers.commands.bonus_commands import register_bonus_commands

    register_bonus_commands(dp)

    # Імпортуємо хендлери кнопок для їх реєстрації (через декоратори)
    from telegram_bot.handlers.common import balance, history, admin, bonus, share_phone

    # Логування зареєстрованих button handlers
    logger.info("Зареєстровано button handlers: %s", list(button_handlers.keys()))

    # Реєстрація button handlers з navigation system
    from telegram_bot.navigation.decorators import get_button_handlers

    for handler_name, handler_func in get_button_handlers().items():
        if menu_manager:
            menu_manager.register_button_handler(handler_name, handler_func)

    logger.info("Всі handlers зареєстровано успішно")


def register_handlers(dp):
    """Стара функція для сумісності"""

    # Реєстрація хендлерів для кнопок
    async def button_router(message: Message):
        # Try using the navigation system first
        menu_manager = dp.get("menu_manager")
        if menu_manager:
            handled = await menu_manager.handle_button(message)
            if handled:
                return

        # Fall back to legacy system if not handled by navigation
        text = message.text
        if text:
            handler_name = text.strip()
            handler = button_handlers.get(handler_name)
            if handler:
                try:
                    await handler(message)
                except Exception as e:
                    logger = logging.getLogger("telegram_bot.handlers.button_router")
                    logger.error("Error in button handler %s: %s", handler_name, e)

    dp.message(F.text)(button_router)  # Route all text messages
