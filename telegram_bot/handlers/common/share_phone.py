from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from telegram_bot.handlers.common.dispatcher import register_button_handler
from telegram_bot.services.supabase import supabase_bonuses_service
import logging


@register_button_handler("share_phone")
async def share_phone(message: Message):
    logger = logging.getLogger("telegram_bot.handlers.share_phone")
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Поділитись номером", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.answer(
        "Натисніть кнопку нижче, щоб поділитися номером телефону:",
        reply_markup=keyboard,
    )

    # Далі номер буде отримано у message.contact.phone_number у /start або echo


async def handle_phone_share(message: Message):
    """Обробка отриманого номера телефону"""
    logger = logging.getLogger("telegram_bot.handlers.handle_phone_share")
    
    if not message.contact:
        await message.answer("❌ Не вдалося отримати номер телефону")
        return
    
    phone_number_raw = message.contact.phone_number
    user_id = message.from_user.id
    
    logger.info(f"Отримано номер телефону {phone_number_raw} від користувача {user_id}")
    
    # Форматуємо номер згідно стандарту
    def format_phone_number(raw_phone):
        """Форматує номер телефону згідно стандарту Poster"""
        # Очищаємо від всіх символів крім цифр
        clean_phone = "".join(filter(str.isdigit, raw_phone))
        
        # Якщо номер починається з +, видаляємо +
        if raw_phone.startswith('+'):
            clean_phone = clean_phone
        
        # Форматований номер з пробілами (+380 98 055 7043)
        if len(clean_phone) >= 12 and clean_phone.startswith('380'):
            formatted_phone = f"+{clean_phone[:3]} {clean_phone[3:5]} {clean_phone[5:8]} {clean_phone[8:12]}"
        else:
            formatted_phone = f"+{clean_phone}"
            
        return formatted_phone, clean_phone
    
    formatted_phone, clean_phone = format_phone_number(phone_number_raw)
    
    # Зберігаємо номер телефону в базу даних
    try:
        from sqlalchemy import create_engine, text
        import os
        
        database_url = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@localhost:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB')}"
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Оновлюємо обидва поля номеру телефону згідно стандарту
            conn.execute(
                text("""
                    UPDATE clients 
                    SET phone = :formatted_phone, 
                        phone_number = :clean_phone,
                        updated_at = NOW()
                    WHERE telegram_user_id = :telegram_user_id
                """),
                {
                    "formatted_phone": formatted_phone,
                    "clean_phone": clean_phone,
                    "telegram_user_id": user_id
                }
            )
            conn.commit()
            
        logger.info(f"Номер телефону збережено: phone='{formatted_phone}', phone_number='{clean_phone}' для користувача {user_id}")
        await message.answer(f"✅ Дякуємо! Ваш номер {formatted_phone} збережено.")
        
    except Exception as e:
        logger.error(f"Помилка збереження номера телефону: {e}")
        await message.answer("❌ Помилка збереження номера телефону")
