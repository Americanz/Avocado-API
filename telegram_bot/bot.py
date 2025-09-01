import asyncio
import logging
from aiogram import Bot, Dispatcher
from telegram_bot.config import settings
from telegram_bot.config.storage import get_storage, close_storage
from telegram_bot.config.redis import close_redis_client, close_async_redis_client
from telegram_bot.handlers.main import register_handlers, register_all_handlers
from telegram_bot.handlers.common.bonus import register_admin_bonus_handlers
from telegram_bot.navigation import MenuManager
from telegram_bot.navigation.decorators import get_button_handlers


async def setup_bot():
    """Налаштування бота при запуску"""
    # Очищаємо кеш при старті бота
    try:
        from telegram_bot.states.phone_state import PhoneState
        PhoneState.clear_all()
        logging.getLogger("telegram_bot").info("Кеш стану телефонів очищено")
    except Exception as e:
        logging.getLogger("telegram_bot").warning(f"Не вдалося очистити кеш: {e}")
    
    # Налаштовуємо команди меню
    from telegram_bot.utils.commands import setup_bot_commands
    await setup_bot_commands()


def main():
    logging.basicConfig(
        level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s"
    )
    logger = logging.getLogger("telegram_bot")
    logger.info("Запуск Telegram-бота...")

    # Initialize navigation system
    menu_manager = MenuManager()

    # Register admin role checker
    menu_manager.register_role_checker("admin", menu_manager._has_admin_role)

    # Register all button handlers with the menu manager
    for handler_name, handler_func in get_button_handlers().items():
        menu_manager.register_button_handler(handler_name, handler_func)

    # Створюємо сховище для станів FSM (Redis або Memory)
    storage = get_storage()

    # Ініціалізуємо бота та диспетчер
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher(storage=storage)

    # Виконуємо початкові налаштування
    asyncio.run(setup_bot())

    # Set menu_manager as a global middleware data
    dp["menu_manager"] = menu_manager

    # СПОЧАТКУ реєструємо FSM обробники (вони мають пріоритет)
    register_admin_bonus_handlers(dp)

    # ПОТІМ реєструємо загальні обробники повідомлень
    register_all_handlers(dp, menu_manager)
    register_handlers(dp)

    logger.info("Handlers зареєстровано. Стартує polling...")

    try:
        asyncio.run(dp.start_polling(bot))
    except KeyboardInterrupt:
        logger.info("Отримано сигнал зупинки...")
    finally:
        # Graceful shutdown
        asyncio.run(shutdown(storage))


async def shutdown(storage):
    """Graceful shutdown function"""
    logger = logging.getLogger("telegram_bot")
    logger.info("Закриваємо з'єднання...")

    # Закриваємо FSM storage
    await close_storage(storage)

    # Закриваємо Redis підключення
    close_redis_client()
    await close_async_redis_client()

    logger.info("Всі з'єднання закрито")


if __name__ == "__main__":
    main()
