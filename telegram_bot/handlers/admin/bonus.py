import logging
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from telegram_bot.handlers.common.permissions import is_admin
from telegram_bot.handlers.common.dispatcher import dispatch_button_handler
from telegram_bot.navigation.decorators import button_handler
from telegram_bot.data.bot_texts import get_text

logger = logging.getLogger("telegram_bot.admin")


@button_handler
async def admin_bonuses(message: Message):
    """Управління бонусами"""
    if not is_admin(message.from_user.id):
        await message.answer(get_text("admin_access_denied") or "⛔️ Доступ лише для адміністратора.")
        return
        
    logger.info(f"admin_bonuses від {message.from_user.id}")
    
    await message.answer(
        get_text("admin_bonuses") or "💰 Управління бонусами\n\nОберіть дію:"
    )


# Обробники add_bonus та remove_bonus знаходяться в common/bonus.py
# з повною FSM логікою для введення даних
