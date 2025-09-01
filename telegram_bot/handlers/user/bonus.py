import logging
from aiogram.types import Message
from telegram_bot.handlers.common.dispatcher import dispatch_button_handler
from telegram_bot.navigation.decorators import button_handler
from telegram_bot.data.bot_texts import get_text

logger = logging.getLogger("telegram_bot.user")


@button_handler
async def view_bonus_history(message: Message):
    """Перегляд історії бонусів користувача"""
    user_id = message.from_user.id
    logger.info(f"view_bonus_history від {user_id}")

    from telegram_bot.services.bonus_service_universal import get_bonus_service

    try:
        bonus_service = get_bonus_service()

        # Спочатку спробуємо знайти клієнта за ID
        user_data = await bonus_service.get_user_by_id(user_id)

        if user_data:
            # Отримуємо повну історію як в check_client_bonus.py
            history = await bonus_service.get_user_history(user_id, limit=5)

            # Розбиваємо на частини, якщо текст занадто довгий
            if len(history) > 4000:
                parts = []
                lines = history.split('\n')
                current_part = ""

                for line in lines:
                    if len(current_part + line + '\n') > 4000:
                        parts.append(current_part)
                        current_part = line + '\n'
                    else:
                        current_part += line + '\n'

                if current_part:
                    parts.append(current_part)

                # Відправляємо частинами
                for i, part in enumerate(parts):
                    if i == 0:
                        await message.answer(part, parse_mode="HTML")
                    else:
                        await message.answer(f"📄 <b>Продовження...</b>\n\n{part}", parse_mode="HTML")
            else:
                await message.answer(history, parse_mode="HTML")
        else:
            await message.answer(
                "� <b>Пошук клієнта</b>\n\n"
                "Для перегляду історії бонусів введіть:\n"
                "• ID клієнта (наприклад: 13763)\n"
                "• Номер телефону\n"
                "• Ім'я клієнта\n\n"
                "Приклад: <code>/history 13763</code>",
                parse_mode="HTML"
            )

    except Exception as e:
        logger.error(f"Помилка при отриманні історії: {e}")
        await message.answer("❌ Сталася помилка при отриманні історії бонусів")


@button_handler
async def view_balance(message: Message):
    """Перегляд балансу користувача"""
    user_id = message.from_user.id
    logger.info(f"view_balance від {user_id}")

    from telegram_bot.services.bonus_service_universal import get_bonus_service

    try:
        bonus_service = get_bonus_service()

        # Пробуємо знайти клієнта за telegram user_id (якщо є прив'язка)
        # Або просимо користувача ввести номер телефону

        # Спочатку спробуємо знайти клієнта за ID
        user_data = await bonus_service.get_user_by_id(user_id)

        if user_data:
            balance = await bonus_service.get_user_balance(user_id)
            if balance is not None:
                if balance == 0:
                    text = get_text("balance_zero") or f"😅 У клієнта #{user_id} поки що немає бонусів"
                else:
                    text = get_text("balance_beauty") or f"✨ Баланс клієнта #{user_id}: <b>{balance:.2f}</b> грн"
                await message.answer(text, parse_mode="HTML")
            else:
                await message.answer("❌ Не вдалося отримати баланс")
        else:
            # Клієнт не знайдений - просимо ввести ID або телефон
            await message.answer(
                "🔍 <b>Пошук клієнта</b>\n\n"
                "Для перегляду бонусів введіть:\n"
                "• ID клієнта (наприклад: 13763)\n"
                "• Номер телефону\n"
                "• Ім'я клієнта\n\n"
                "Приклад: <code>/bonus 13763</code>",
                parse_mode="HTML"
            )

    except Exception as e:
        logger.error(f"Помилка при отриманні балансу: {e}")
        await message.answer("❌ Сталася помилка при отриманні балансу")
