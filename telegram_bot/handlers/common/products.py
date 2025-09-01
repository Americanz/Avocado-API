import logging
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from telegram_bot.handlers.common.dispatcher import register_button_handler
from telegram_bot.services.bonus_service_universal import get_bonus_service
from telegram_bot.data.bot_texts import get_text


@register_button_handler("show_products")
async def show_products_catalog(message: Message):
    """Показати каталог товарів"""
    logger = logging.getLogger("telegram_bot.handlers.products")
    user_id = message.from_user.id
    logger.info(f"show_products для user_id={user_id}")
    
    try:
        bonus_service = get_bonus_service()
        
        # Отримуємо категорії товарів
        categories = await bonus_service.get_product_categories()
        
        if not categories:
            await message.answer("📦 Каталог товарів поки що порожній.")
            return
        
        # Створюємо клавіатуру з категоріями
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        for category in categories:
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"📦 {category}",
                    callback_data=f"category:{category}"
                )
            ])
        
        # Додаємо кнопку улюблених товарів
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="❤️ Мої улюблені товари",
                callback_data="show_favorites"
            )
        ])
        
        # Додаємо кнопку історії покупок
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="🛒 Історія покупок",
                callback_data="show_purchase_history"
            )
        ])
        
        await message.answer(
            "🛍️ <b>Каталог товарів</b>\n\n"
            "Оберіть категорію товарів для перегляду:",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Помилка при отриманні каталогу: {e}")
        await message.answer(f"Помилка при отриманні каталогу: {str(e)}")


@register_button_handler("show_favorites")
async def show_user_favorites(message: Message):
    """Показати улюблені товари користувача"""
    logger = logging.getLogger("telegram_bot.handlers.products")
    user_id = message.from_user.id
    logger.info(f"show_favorites для user_id={user_id}")
    
    try:
        bonus_service = get_bonus_service()
        favorites = await bonus_service.get_user_favorites(user_id)
        
        if not favorites:
            await message.answer(
                "❤️ <b>Улюблені товари</b>\n\n"
                "У вас поки що немає улюблених товарів.\n"
                "Додавайте товари в улюблені під час покупок!",
                parse_mode="HTML"
            )
            return
        
        text = "❤️ <b>Ваші улюблені товари:</b>\n\n"
        
        for i, item in enumerate(favorites, 1):
            text += f"{i}. <b>{item['name']}</b>\n"
            if item.get('brand'):
                text += f"   🏷️ {item['brand']}\n"
            text += f"   📦 {item['category']}\n"
            if item.get('base_price'):
                text += f"   💰 {item['base_price']:.2f} грн\n"
            if item.get('notes'):
                text += f"   📝 {item['notes']}\n"
            text += "\n"
        
        await message.answer(text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Помилка при отриманні улюблених: {e}")
        await message.answer(f"Помилка при отриманні улюблених: {str(e)}")


@register_button_handler("show_purchase_history")  
async def show_purchase_history(message: Message):
    """Показати історію покупок користувача"""
    logger = logging.getLogger("telegram_bot.handlers.products")
    user_id = message.from_user.id
    logger.info(f"show_purchase_history для user_id={user_id}")
    
    try:
        bonus_service = get_bonus_service()
        history = await bonus_service.get_purchase_history(user_id, limit=20)
        
        if not history:
            await message.answer(
                "🛒 <b>Історія покупок</b>\n\n"
                "У вас поки що немає історії покупок.",
                parse_mode="HTML"
            )
            return
        
        text = "🛒 <b>Ваші останні покупки:</b>\n\n"
        
        current_receipt = None
        for item in history:
            # Групуємо по чеках
            if current_receipt != item.get('receipt_id'):
                current_receipt = item.get('receipt_id')
                if item.get('receipt_number'):
                    text += f"🧾 <b>Чек #{item['receipt_number']}</b>\n"
                if item.get('store_name'):
                    text += f"🏪 {item['store_name']}\n"
                text += f"📅 {item['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
            
            # Товар
            text += f"   • <b>{item['product_name']}</b>\n"
            text += f"     Кількість: {item['quantity']}\n"
            text += f"     Ціна: {item['unit_price']:.2f} грн\n"
            text += f"     Бонуси: +{item['bonus_earned']}\n\n"
            
            # Обмежуємо довжину повідомлення
            if len(text) > 3500:
                text += "...\n<i>Показано лише останні покупки</i>"
                break
        
        await message.answer(text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Помилка при отриманні історії покупок: {e}")
        await message.answer(f"Помилка при отриманні історії покупок: {str(e)}")
