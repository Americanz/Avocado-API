import logging
from datetime import datetime, timedelta
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from telegram_bot.handlers.common.permissions import is_admin
from telegram_bot.handlers.common.dispatcher import register_button_handler
from telegram_bot.data.bot_texts import get_text
from src.features.telegram_bot.poster.service import get_poster_service

logger = logging.getLogger("telegram_bot.admin.poster")


@register_button_handler("poster_sync")
async def poster_sync_menu(message: Message):
    """Меню синхронізації з Poster"""
    if not is_admin(message.from_user.id):
        await message.answer(
            get_text("admin_access_denied") or "⛔️ Доступ лише для адміністратора."
        )
        return

    logger.info(f"poster_sync_menu від {message.from_user.id}")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📥 Синхронізувати транзакції",
                    callback_data="sync_transactions",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Статистика синхронізації", callback_data="sync_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Автосинхронізація", callback_data="auto_sync_settings"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Налаштування Poster", callback_data="poster_settings"
                )
            ],
        ]
    )

    await message.answer(
        "🏪 <b>Інтеграція з Poster</b>\n\n" "Оберіть дію для роботи з системою Poster:",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


@register_button_handler("sync_transactions")
async def sync_transactions(message: Message):
    """Синхронізація транзакцій з Poster"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Доступ заборонено.")
        return

    logger.info(f"sync_transactions від {message.from_user.id}")

    # Показуємо повідомлення про початок синхронізації
    status_msg = await message.answer("🔄 Розпочинаю синхронізацію з Poster...")

    try:
        poster_service = await get_poster_service()
        if not poster_service:
            await status_msg.edit_text(
                "❌ <b>Помилка конфігурації</b>\n\n"
                "Не налаштовані параметри підключення до Poster API.\n"
                "Зверніться до адміністратора системи.",
                parse_mode="HTML",
            )
            return

        # Синхронізуємо транзакції за останні 7 днів
        date_from = datetime.now() - timedelta(days=7)
        date_to = datetime.now()

        await status_msg.edit_text("📡 Отримую дані з Poster API...")

        # Отримуємо транзакції
        transactions = await poster_service.get_transactions(date_from, date_to)

        if not transactions:
            await status_msg.edit_text(
                "📭 <b>Синхронізація завершена</b>\n\n" "Нових транзакцій не знайдено.",
                parse_mode="HTML",
            )
            return

        await status_msg.edit_text(
            f"💾 Зберігаю {len(transactions)} транзакцій в базу даних..."
        )

        # Синхронізуємо в базу даних
        start_time = datetime.utcnow()
        stats = poster_service.sync_transactions_to_db(transactions)

        # Логуємо результат
        poster_service.log_sync_result(
            "transactions", "success", {**stats, "start_time": start_time}
        )

        # Показуємо результат
        result_text = (
            "✅ <b>Синхронізація завершена</b>\n\n"
            f"📊 <b>Статистика:</b>\n"
            f"• Оброблено: {stats['processed']}\n"
            f"• Створено нових: {stats['created']}\n"
            f"• Оновлено: {stats['updated']}\n"
            f"• Помилок: {stats['errors']}\n\n"
            f"📅 Період: {date_from.strftime('%d.%m.%Y')} - {date_to.strftime('%d.%m.%Y')}"
        )

        await status_msg.edit_text(result_text, parse_mode="HTML")

        # Додатково синхронізуємо продукти для нових транзакцій
        if stats["created"] > 0:
            await message.answer("🛍️ Синхронізую продукти для нових транзакцій...")
            # Тут можна додати логіку синхронізації продуктів

    except Exception as e:
        logger.error(f"Помилка синхронізації: {e}")
        await status_msg.edit_text(
            f"❌ <b>Помилка синхронізації</b>\n\n"
            f"Деталі: {str(e)}\n\n"
            f"Зверніться до адміністратора.",
            parse_mode="HTML",
        )


@register_button_handler("sync_stats")
async def sync_statistics(message: Message):
    """Статистика синхронізації"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Доступ заборонено.")
        return

    logger.info(f"sync_stats від {message.from_user.id}")

    try:
        poster_service = await get_poster_service()
        if not poster_service:
            await message.answer("❌ Сервіс Poster не налаштований.")
            return

        # Отримуємо статистику з бази даних
        with poster_service.SessionLocal() as db:
            from src.features.telegram_bot.models import (
                Transaction,
                SyncLog,
            )

            # Загальна статистика транзакцій
            total_transactions = db.query(Transaction).count()
            synced_to_telegram = (
                db.query(Transaction)
                .filter(Transaction.is_synced_to_telegram == True)
                .count()
            )

            # Останні синхронізації
            recent_syncs = (
                db.query(SyncLog).order_by(SyncLog.created_at.desc()).limit(5).all()
            )

        # Формуємо повідомлення
        stats_text = (
            "📊 <b>Статистика синхронізації Poster</b>\n\n"
            f"🏪 <b>Транзакції:</b>\n"
            f"• Всього в базі: {total_transactions}\n"
            f"• Синхронізовано з ботом: {synced_to_telegram}\n"
            f"• Не синхронізовано: {total_transactions - synced_to_telegram}\n\n"
        )

        if recent_syncs:
            stats_text += "🔄 <b>Останні синхронізації:</b>\n"
            for sync in recent_syncs:
                status_emoji = "✅" if sync.status == "success" else "❌"
                stats_text += (
                    f"{status_emoji} {sync.sync_type} - "
                    f"{sync.created_at.strftime('%d.%m %H:%M')}\n"
                    f"   Записів: {sync.records_success}/{sync.records_processed}\n"
                )

        await message.answer(stats_text, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Помилка отримання статистики: {e}")
        await message.answer(f"❌ Помилка: {str(e)}")


@register_button_handler("poster_settings")
async def poster_settings(message: Message):
    """Налаштування Poster"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Доступ заборонено.")
        return

    logger.info(f"poster_settings від {message.from_user.id}")

    try:
        from src.config.settings import get_settings

        settings = get_settings()

        # Перевіряємо налаштування
        api_token = getattr(settings, "POSTER_API_TOKEN", None)
        account_name = getattr(settings, "POSTER_ACCOUNT_NAME", None)

        token_status = "✅ Налаштований" if api_token else "❌ Не налаштований"
        account_status = "✅ Налаштований" if account_name else "❌ Не налаштований"

        settings_text = (
            "⚙️ <b>Налаштування Poster API</b>\n\n"
            f"🔑 <b>API Token:</b> {token_status}\n"
            f"🏢 <b>Account Name:</b> {account_status}\n\n"
        )

        if api_token and account_name:
            settings_text += (
                f"🌐 <b>API URL:</b>\n"
                f"https://{account_name}.joinposter.com/api\n\n"
                "✅ Конфігурація готова для роботи"
            )
        else:
            settings_text += (
                "⚠️ <b>Для роботи з Poster потрібно:</b>\n"
                "1. Налаштувати POSTER_API_TOKEN\n"
                "2. Налаштувати POSTER_ACCOUNT_NAME\n"
                "3. Перезапустити бота\n\n"
                "Зверніться до адміністратора системи."
            )

        await message.answer(settings_text, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Помилка налаштувань: {e}")
        await message.answer(f"❌ Помилка: {str(e)}")
