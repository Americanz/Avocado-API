import logging
from aiogram.types import Message
from telegram_bot.handlers.common.dispatcher import register_button_handler
from telegram_bot.services.bonus_service_universal import get_bonus_service


@register_button_handler("show_history")
async def show_history(message: Message):
    logger = logging.getLogger("telegram_bot.handlers.history")
    user_id = message.from_user.id
    logger.info(f"show_history для user_id={user_id}")
    try:
        bonus_service = get_bonus_service()
        history = await bonus_service.get_user_history(user_id)
        
        # PostgreSQL сервіс повертає готову строку з історією
        if isinstance(history, str):
            await message.answer(history, parse_mode="HTML")
            return
        
        from telegram_bot.data.bot_texts import get_text

        if not history:
            text = get_text("history_empty") or "Історія бонусів порожня."
            await message.answer(text)
            return

        # Формуємо детальну історію з інформацією про магазини (для інших сервісів)
        items = []
        for item in history:
            # Форматуємо дату
            date_str = item.get("created_at", "").strftime("%d.%m.%Y %H:%M") if item.get("created_at") else ""
            
            # Основна інформація
            amount = item.get("amount", 0)
            amount_str = f"+{amount}" if amount > 0 else str(amount)
            
            # Інформація про магазин і чек
            store_info = ""
            if item.get("store_name"):
                store_info = f"\n🏪 {item['store_name']}"
                if item.get("store_address"):
                    # Скорочуємо адресу для компактності
                    address = item['store_address']
                    if len(address) > 30:
                        address = address[:27] + "..."
                    store_info += f"\n📍 {address}"
            
            receipt_info = ""
            if item.get("receipt_number"):
                receipt_info = f"\n🧾 Чек #{item['receipt_number']}"
                if item.get("receipt_total"):
                    receipt_info += f" на {item['receipt_total']:.2f} грн"
            
            # Складаємо повний запис
            history_entry = f"📅 {date_str}\n💰 {amount_str} бонусів"
            if store_info:
                history_entry += store_info
            if receipt_info:
                history_entry += receipt_info
            
            # Додаємо опис якщо є
            if item.get("description") and not item.get("store_name"):
                history_entry += f"\n📝 {item['description']}"
            
            items.append(history_entry)

        # Відправляємо історію частинами якщо вона довга
        text = "📊 <b>Історія ваших бонусів:</b>\n\n" + "\n\n➖➖➖➖➖\n\n".join(items)
        
        # Telegram має ліміт повідомлень ~4000 символів
        if len(text) > 3800:
            # Розділяємо на частини
            parts = []
            current_part = "📊 <b>Історія ваших бонусів:</b>\n\n"
            
            for item in items:
                if len(current_part + item + "\n\n➖➖➖➖➖\n\n") > 3800:
                    parts.append(current_part.rstrip("\n\n➖➖➖➖➖\n\n"))
                    current_part = item + "\n\n➖➖➖➖➖\n\n"
                else:
                    current_part += item + "\n\n➖➖➖➖➖\n\n"
            
            if current_part.strip():
                parts.append(current_part.rstrip("\n\n➖➖➖➖➖\n\n"))
            
            # Відправляємо частинами
            for i, part in enumerate(parts):
                if i > 0:
                    part = f"📊 <b>Історія ваших бонусів (частина {i+1}):</b>\n\n" + part.split("\n\n", 1)[1] if "\n\n" in part else part
                await message.answer(part, parse_mode="HTML")
        else:
            await message.answer(text, parse_mode="HTML")
            
    except Exception as e:
        logger.error(f"Помилка при отриманні історії: {e}")
        await message.answer(f"Помилка при отриманні історії: {str(e)}")
