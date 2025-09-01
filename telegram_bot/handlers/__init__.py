# Імпорти з нової структури
from telegram_bot.handlers.common.dispatcher import button_handlers
from telegram_bot.handlers.user.basic import register_user_handlers
from telegram_bot.handlers.user.bonus import *
from telegram_bot.handlers.admin.panel import *
from telegram_bot.handlers.admin.bonus import *

# Poster integration handlers
from telegram_bot.handlers.procedures.bonus import register_bonus_handlers
from telegram_bot.handlers.procedures.history import register_history_handlers

# Старі імпорти для сумісності
from telegram_bot.handlers.common.balance import *
from telegram_bot.handlers.common.history import *
from telegram_bot.handlers.common.admin import *
from telegram_bot.handlers.common.bonus import *


def register_handlers(dp):
    # Register Poster integration handlers
    register_bonus_handlers(dp)
    register_history_handlers(dp)
    
    # Register user handlers
    register_user_handlers(dp)
    
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

        # Fall back to legacy system if not handled by navigation
        text = message.text
        handler = button_handlers.get(text)
        if handler:
            await handler(message)

    dp.message(F.text)(button_router)  # Route all text messages
