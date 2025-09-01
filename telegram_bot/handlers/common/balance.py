import logging
from aiogram.types import Message
from telegram_bot.handlers.common.dispatcher import register_button_handler
from telegram_bot.services.bonus_service_universal import get_bonus_service


@register_button_handler("show_balance")
async def show_balance(message: Message):
    logger = logging.getLogger("telegram_bot.handlers.balance")
    user_id = message.from_user.id
    logger.info(f"show_balance для user_id={user_id}")
    try:
        bonus_service = get_bonus_service()
        balance = await bonus_service.get_user_balance(user_id)
        from telegram_bot.data.bot_texts import get_text

        if balance == 0:
            text = get_text("balance_zero") or "У вас поки що немає бонусів."
            await message.answer(text)
        else:
            text = (
                get_text("balance_beauty") or f"Ваш баланс: <b>{balance}</b> бонусів!"
            )
            await message.answer(text.format(balance=balance), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Помилка при отриманні балансу: {e}")
        await message.answer(str(e))
