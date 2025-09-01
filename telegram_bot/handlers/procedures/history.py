"""
Telegram bot handlers for purchase history
"""

from aiogram import types
from aiogram.filters.command import Command
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_
from datetime import datetime, timedelta
import logging

from src.core.database.connection import get_db
from src.features.telegram_bot.schemas import (
    get_telegram_user,
    get_user_receipts,
    get_receipt_details,
    get_monthly_receipts_stats,
    get_user_purchase_history,
)

logger = logging.getLogger(__name__)


async def cmd_purchase_history(message: types.Message, session: Session = None):
    """Show user's purchase history"""
    if not session:
        session = next(get_db())

    try:
        user_id = message.from_user.id

        # Find user using schema
        user = get_telegram_user(session, user_id)

        if not user:
            await message.answer(
                "❌ Вас не знайдено в системі. Спочатку зареєструйтеся командою /register"
            )
            return

        # Get user receipts using schema
        receipts = get_user_receipts(session, user_id, limit=10)

        if not receipts:
            await message.answer("📭 У вас поки що немає історії покупок")
            return

        response = "🛍️ **Ваші останні покупки:**\n\n"

        total_spent = 0
        total_bonuses = 0

        for receipt in receipts:
            date_str = (
                receipt["date_created"].strftime("%d.%m.%Y %H:%M")
                if receipt["date_created"]
                else "Не вказано"
            )
            store_name = receipt["store_name"] or "Невідомий магазин"

            response += f"🏪 **{store_name}**\n"
            response += f"📅 {date_str}\n"
            response += f"💰 Сума: {receipt['total_amount']} грн\n"
            response += f"💸 Знижка: {receipt['discount']} грн\n"
            response += f"🧾 Чек: #{receipt['receipt_number']}\n\n"

            total_spent += float(receipt["total_amount"])
            # Бонуси можемо розрахувати як відсоток від суми
            bonus_amount = int(float(receipt["total_amount"]) * 0.01)  # 1% від суми
            total_bonuses += bonus_amount

        response += f"📊 **Загальна статистика:**\n"
        response += f"• Витрачено: {total_spent:.2f} грн\n"
        response += f"• Отримано бонусів: {total_bonuses}\n"

        await message.answer(response, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in purchase history command: {e}")
        await message.answer("❌ Помилка отримання історії покупок. Спробуйте пізніше.")
    finally:
        session.close()


async def cmd_receipt_details(message: types.Message, session: Session = None):
    """Show details of specific receipt"""
    if not session:
        session = next(get_db())

    try:
        # Extract receipt number from command
        command_parts = message.text.split()
        if len(command_parts) < 2:
            await message.answer(
                "📋 Використання: /receipt <номер_чека>\nПриклад: /receipt 12345"
            )
            return

        transaction_id = command_parts[1]
        user_id = message.from_user.id

        # Find user
        user = session.query(Client).filter(Client.telegram_user_id == user_id).first()

        if not user:
            await message.answer("❌ Вас не знайдено в системі")
            return

        # Find transaction
        transaction = (
            session.query(Transaction)
            .filter(
                and_(
                    Transaction.client_phone == user.phone,
                    Transaction.transaction_id == int(transaction_id),
                )
            )
            .first()
        )

        if not transaction:
            await message.answer(f"❌ Чек #{transaction_id} не знайдено")
            return

        # Format transaction details
        date_str = (
            transaction.date_close.strftime("%d.%m.%Y %H:%M")
            if transaction.date_close
            else "Не вказано"
        )
        store_name = transaction.spot_name or f"Точка {transaction.spot_id}"

        response = f"🧾 **Чек #{transaction.transaction_id}**\n\n"
        response += f"🏪 Магазин: {store_name}\n"
        response += f"📅 Дата: {date_str}\n"
        response += f"💰 Загальна сума: {transaction.sum} грн\n"
        response += f"💸 Знижка: {transaction.discount} грн\n"
        response += f"🎁 Нараховано бонусів: {transaction.bonus}\n\n"

        # Get transaction products
        products = (
            session.query(TransactionProduct)
            .filter(TransactionProduct.transaction_id == transaction.transaction_id)
            .all()
        )

        if products:
            response += "📦 **Товари:**\n"
            for product in products:
                response += f"• {product.product_name}\n"
                response += f"  {product.count} x {product.price} = {product.sum} грн\n"
        else:
            response += "📦 Деталі товарів недоступні\n"

        await message.answer(response, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in receipt details command: {e}")
        await message.answer("❌ Помилка отримання деталей чека. Спробуйте пізніше.")
    finally:
        session.close()


async def cmd_monthly_stats(message: types.Message, session: Session = None):
    """Show monthly purchase statistics"""
    if not session:
        session = next(get_db())

    try:
        user_id = message.from_user.id

        # Find user
        user = session.query(Client).filter(Client.telegram_user_id == user_id).first()

        if not user:
            await message.answer("❌ Вас не знайдено в системі")
            return

        # Get transactions for current month
        start_of_month = datetime.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        transactions = (
            session.query(Transaction)
            .filter(
                and_(
                    Transaction.client_phone == user.phone,
                    Transaction.date_close >= start_of_month,
                )
            )
            .all()
        )

        if not transactions:
            await message.answer("📅 У поточному місяці ще немає покупок")
            return

        # Calculate statistics
        total_amount = sum(float(t.sum) for t in transactions)
        total_bonuses = sum(t.bonus for t in transactions)
        purchase_count = len(transactions)
        average_check = total_amount / purchase_count if purchase_count > 0 else 0

        # Get store statistics
        store_stats = {}
        for transaction in transactions:
            store_name = transaction.spot_name or f"Точка {transaction.spot_id}"
            if store_name not in store_stats:
                store_stats[store_name] = {"count": 0, "amount": 0}
            store_stats[store_name]["count"] += 1
            store_stats[store_name]["amount"] += float(transaction.sum)

        month_name = start_of_month.strftime("%B %Y")

        response = f"📊 **Статистика за {month_name}:**\n\n"
        response += f"🛍️ Покупок: {purchase_count}\n"
        response += f"💰 Витрачено: {total_amount:.2f} грн\n"
        response += f"🎁 Отримано бонусів: {total_bonuses}\n"
        response += f"📈 Середній чек: {average_check:.2f} грн\n\n"

        if store_stats:
            response += "🏪 **По магазинах:**\n"
            for store_name, stats in store_stats.items():
                response += f"• {store_name}: {stats['count']} покупок, {stats['amount']:.2f} грн\n"

        await message.answer(response, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in monthly stats command: {e}")
        await message.answer("❌ Помилка отримання статистики. Спробуйте пізніше.")
    finally:
        session.close()


async def cmd_favorite_products(message: types.Message, session: Session = None):
    """Show user's most purchased products"""
    if not session:
        session = next(get_db())

    try:
        user_id = message.from_user.id

        # Find user
        user = session.query(Client).filter(Client.telegram_user_id == user_id).first()

        if not user:
            await message.answer("❌ Вас не знайдено в системі")
            return

        # Get popular products from user's transactions
        from sqlalchemy import func

        popular_products = (
            session.query(
                TransactionProduct.product_name,
                func.count(TransactionProduct.id).label("purchase_count"),
                func.sum(TransactionProduct.sum).label("total_spent"),
                func.sum(TransactionProduct.count).label("total_quantity"),
            )
            .join(
                Transaction,
                TransactionProduct.transaction_id == Transaction.transaction_id,
            )
            .filter(Transaction.client_phone == user.phone)
            .group_by(TransactionProduct.product_name)
            .order_by(desc("purchase_count"))
            .limit(10)
            .all()
        )

        if not popular_products:
            await message.answer("📭 Поки що немає даних про улюблені товари")
            return

        response = "⭐ **Ваші найпопулярніші товари:**\n\n"

        for i, product in enumerate(popular_products, 1):
            response += f"{i}. **{product.product_name}**\n"
            response += f"   Куплено: {product.purchase_count} разів\n"
            response += f"   Витрачено: {float(product.total_spent):.2f} грн\n"
            response += f"   Кількість: {float(product.total_quantity):.1f}\n\n"

        await message.answer(response, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in favorite products command: {e}")
        await message.answer(
            "❌ Помилка отримання улюблених товарів. Спробуйте пізніше."
        )
    finally:
        session.close()


# Register handlers
def register_history_handlers(dp):
    """Register history-related handlers"""
    dp.message.register(cmd_purchase_history, Command("purchases"))
    dp.message.register(cmd_receipt_details, Command("receipt"))
    dp.message.register(cmd_monthly_stats, Command("stats"))
    dp.message.register(cmd_favorite_products, Command("favorites"))
