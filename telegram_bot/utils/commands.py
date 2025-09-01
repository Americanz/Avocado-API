"""
Утиліти для управління командами бота
"""

import asyncio
from aiogram import Bot
from aiogram.types import BotCommand
import logging

logger = logging.getLogger(__name__)


def _get_settings():
    """Отримуємо settings без циклічного імпорту"""
    from telegram_bot.config import settings

    return settings


async def clear_bot_commands(bot: Bot):
    """Очистити всі команди з меню бота"""
    try:
        await bot.set_my_commands([])
        logger.info("✅ Всі команди очищено з меню бота")
        return True
    except Exception as e:
        logger.error(f"❌ Помилка при очищенні команд: {e}")
        return False


async def set_bot_commands(bot: Bot):
    """Встановити команди для бота"""
    commands = [
        BotCommand(command="start", description="🏠 Головне меню"),
        BotCommand(command="redis", description="🔴 Статус Redis & Логування"),
    ]

    try:
        await bot.set_my_commands(commands)
        logger.info("✅ Команди встановлено успішно:")

        # Перевіряємо встановлені команди
        current_commands = await bot.get_my_commands()
        for cmd in current_commands:
            logger.info(f"📌 /{cmd.command} - {cmd.description}")
        return True

    except Exception as e:
        logger.error(f"❌ Помилка при встановленні команд: {e}")
        return False


async def get_current_commands(bot: Bot):
    """Отримати поточні команди бота"""
    try:
        current_commands = await bot.get_my_commands()
        logger.info("📋 Поточні команди бота:")

        if not current_commands:
            logger.info("   (Немає команд)")
        else:
            for cmd in current_commands:
                logger.info(f"   /{cmd.command} - {cmd.description}")

        return current_commands

    except Exception as e:
        logger.error(f"❌ Помилка при отриманні команд: {e}")
        return []


async def setup_bot_commands():
    """Налаштування команд при запуску бота"""
    settings = _get_settings()
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

    try:
        # Очищуємо старі команди
        await clear_bot_commands(bot)

        # Встановлюємо нові
        await set_bot_commands(bot)

    finally:
        await bot.session.close()


if __name__ == "__main__":
    # Якщо запускаємо як окремий скрипт
    logging.basicConfig(
        level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s"
    )

    asyncio.run(setup_bot_commands())
