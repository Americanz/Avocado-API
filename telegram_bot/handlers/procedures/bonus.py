"""
Telegram bot handlers for bonus operations
"""

from aiogram import types, F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from src.core.database.connection import get_db
from src.features.telegram_bot.schemas import (
    get_telegram_user,
    create_or_update_telegram_user,
    get_user_bonus_balance,
    get_user_bonus_history,
    add_bonus_to_user,
    create_or_get_bonus_account
)

logger = logging.getLogger(__name__)


class BonusStates(StatesGroup):
    waiting_for_phone = State()


async def cmd_bonus_balance(message: types.Message, session: Session = None):
    """Show user's bonus balance"""
    if not session:
        session = next(get_db())

    try:
        user_id = message.from_user.id

        # Find user using schema
        user = get_telegram_user(session, user_id)

        if not user:
            await message.answer(
                "❌ Вас не знайдено в системі. Спочатку поділіться своїм номером телефону командою /register"
            )
            return

        # Get bonus balance using schema
        balance = get_user_bonus_balance(session, user_id)

        if balance == 0:
            # Check if account exists, if not create it
            bonus_account = create_or_get_bonus_account(session, user_id)

        # Get recent transactions using schema
        recent_transactions = get_user_bonus_history(session, user_id, limit=5)

        # Format response
        response = f"💰 **Ваш бонусний баланс: {balance:.1f} бонусів**\n\n"

        if recent_transactions:
            response += "📋 Останні операції:\n"
            for trans in recent_transactions:
                date_str = trans['created_at'].strftime("%d.%m.%Y %H:%M")
                amount_str = f"+{trans['amount']}" if trans['amount'] > 0 else str(trans['amount'])
                response += f"• {date_str}: {amount_str} ({trans['description']})\n"
        else:
            response += "📭 Поки що немає бонусних операцій"

        await message.answer(response, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in bonus balance command: {e}")
        await message.answer("❌ Помилка отримання балансу. Спробуйте пізніше.")
    finally:
        session.close()


async def cmd_bonus_history(message: types.Message, session: Session = None):
    """Show user's bonus history"""
    if not session:
        session = next(get_db())

    try:
        user_id = message.from_user.id

        # Get all bonus transactions using schema
        transactions = get_user_bonus_history(session, user_id, limit=20)

        if not transactions:
            await message.answer("📭 У вас поки що немає бонусних операцій")
            return

        response = "📊 **Історія бонусних операцій:**\n\n"

        total_earned = 0
        total_spent = 0

        for trans in transactions:
            date_str = trans['created_at'].strftime("%d.%m.%Y %H:%M")
            amount_str = f"+{trans['amount']}" if trans['amount'] > 0 else str(trans['amount'])

            if trans['amount'] > 0:
                total_earned += trans['amount']
                emoji = "💚"
            else:
                total_spent += abs(trans['amount'])
                emoji = "💸"

            response += f"{emoji} {date_str}: {amount_str}\n"
            response += f"   _{trans['description']}_\n\n"

        response += f"📈 **Статистика:**\n"
        response += f"• Зароблено: {total_earned} бонусів\n"
        response += f"• Витрачено: {total_spent} бонусів\n"

        await message.answer(response, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in bonus history command: {e}")
        await message.answer("❌ Помилка отримання історії. Спробуйте пізніше.")
    finally:
        session.close()


async def cmd_register_phone(message: types.Message, state: FSMContext):
    """Register user phone for bonus system"""
    await message.answer(
        "📱 Для активації бонусної програми поділіться своїм номером телефону",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="📱 Поділитися номером", request_contact=True)]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    await state.set_state(BonusStates.waiting_for_phone)


async def process_contact(message: types.Message, state: FSMContext, session: Session = None):
    """Process shared contact"""
    if not session:
        session = next(get_db())

    try:
        if not message.contact:
            await message.answer("❌ Не вдалося отримати контакт. Спробуйте ще раз.")
            return

        user_id = message.from_user.id
        phone = message.contact.phone_number

        # Clean phone number
        phone = phone.replace("+", "").replace("-", "").replace(" ", "")

        # Create or update user using schema
        user = create_or_update_telegram_user(
            session,
            telegram_user_id=user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            phone=phone
        )

        # Create or get bonus account using schema
        bonus_account = create_or_get_bonus_account(session, user_id)
        balance = get_user_bonus_balance(session, user_id)

        await message.answer(
            f"✅ Номер телефону {phone} успішно зареєстровано!\n"
            f"💰 Ваш бонусний баланс: {balance:.1f} бонусів\n\n"
            f"Тепер ви будете отримувати бонуси за покупки!",
            reply_markup=types.ReplyKeyboardRemove()
        )

        await state.clear()

    except Exception as e:
        logger.error(f"Error processing contact: {e}")
        await message.answer("❌ Помилка реєстрації. Спробуйте пізніше.")
    finally:
        session.close()


async def cmd_bonus_info(message: types.Message):
    """Show bonus program information"""
    info_text = """
🎁 **Бонусна програма**

💰 **Як працює:**
• За кожну покупку ви отримуєте бонуси
• 1 гривня = 1 бонус
• Бонуси можна використовувати для оплати

📱 **Команди:**
• /bonus - баланс бонусів
• /bonus_history - історія операцій
• /purchases - історія покупок
• /register - реєстрація номера телефону

💡 **Примітка:** Бонуси нараховуються автоматично при покупках в наших магазинах.
"""

    await message.answer(info_text, parse_mode="Markdown")


# Register handlers
def register_bonus_handlers(dp):
    """Register bonus-related handlers"""
    dp.message.register(cmd_bonus_balance, Command("bonus"))
    dp.message.register(cmd_bonus_history, Command("bonus_history"))
    dp.message.register(cmd_register_phone, Command("register"))
    dp.message.register(cmd_bonus_info, Command("bonus_info"))
    dp.message.register(process_contact, F.contact, BonusStates.waiting_for_phone)
