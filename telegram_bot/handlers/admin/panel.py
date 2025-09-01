import logging
from aiogram.types import Message
from telegram_bot.handlers.common.permissions import is_admin
from telegram_bot.handlers.common.dispatcher import dispatch_button_handler
from telegram_bot.navigation.decorators import button_handler
from telegram_bot.data.bot_texts import get_text
from telegram_bot.utils.logging import log_admin_action

logger = logging.getLogger("telegram_bot.admin")


@button_handler
async def admin_panel(message: Message):
    """Головна панель адміністратора"""
    if not is_admin(message.from_user.id):
        await message.answer(get_text("admin_access_denied") or "⛔️ Доступ лише для адміністратора.")
        return
        
    log_admin_action(message, "admin_panel")
    
    await message.answer(
        get_text("admin_panel") or "🔧 Панель адміністратора\n\nОберіть дію з меню нижче:"
    )


@button_handler
async def admin_stats(message: Message):
    """Статистика системи"""
    if not is_admin(message.from_user.id):
        await message.answer(get_text("admin_access_denied") or "⛔️ Доступ лише для адміністратора.")
        return
        
    logger.info(f"admin_stats від {message.from_user.id}")
    
    from telegram_bot.services.bonus_service_universal import get_bonus_service
    
    try:
        bonus_service = get_bonus_service()
        # Тут буде логіка збору статистики
        stats_text = get_text("admin_stats") or "📊 Статистика системи:"
        stats_text += "\n\n👥 Користувачі: -\n💰 Загальний баланс: -\n📈 Транзакції: -"
        
        await message.answer(stats_text)
    except Exception as e:
        logger.error(f"Помилка при отриманні статистики: {e}")
        await message.answer(get_text("admin_stats_error") or "❌ Помилка при отриманні статистики")


@button_handler
async def admin_users(message: Message):
    """Управління користувачами"""
    if not is_admin(message.from_user.id):
        await message.answer(get_text("admin_access_denied") or "⛔️ Доступ лише для адміністратора.")
        return
        
    logger.info(f"admin_users від {message.from_user.id}")
    
    await message.answer(
        get_text("admin_users") or "👥 Управління користувачами\n\n(Тут буде список користувачів)"
    )


@button_handler
async def admin_back(message: Message):
    """Повернення до попереднього меню"""
    if not is_admin(message.from_user.id):
        await message.answer(get_text("admin_access_denied") or "⛔️ Доступ лише для адміністратора.")
        return
        
    log_admin_action(message, "admin_back")
    
    # Показуємо головне меню без додаткових повідомлень
    from telegram_bot.data.keyboards import get_keyboard
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    
    # Формуємо клавіатуру
    keyboard_buttons = []
    for btn in get_keyboard("main"):
        if btn["enabled"]:
            keyboard_buttons.append([KeyboardButton(text=btn["text"])])
    
    # Додаємо адмін кнопки
    for btn in get_keyboard("admin"):
        if btn["enabled"]:
            keyboard_buttons.append([KeyboardButton(text=btn["text"])])

    keyboard = ReplyKeyboardMarkup(keyboard=keyboard_buttons, resize_keyboard=True)
    
    await message.answer(
        get_text("back_to_menu") or "↩️ Головне меню",
        reply_markup=keyboard
    )


@button_handler
async def admin_back_to_panel(message: Message):
    """Повернення до панелі адміністратора"""
    if not is_admin(message.from_user.id):
        await message.answer(get_text("admin_access_denied") or "⛔️ Доступ лише для адміністратора.")
        return
        
    logger.info(f"admin_back_to_panel від {message.from_user.id}")
    
    await dispatch_button_handler("admin_panel", message)
