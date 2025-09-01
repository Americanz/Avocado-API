#!/usr/bin/env python3
"""
Комплексний аналіз продажів: зведений звіт
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


async def comprehensive_sales_analysis():
    """Комплексний аналіз продажів"""
    from src.core.database.connection import AsyncSessionLocal
    from src.features.telegram_bot.models.spot import Spot
    from src.features.telegram_bot.models.transaction import Transaction
    from src.features.telegram_bot.models.client import Client
    from src.features.telegram_bot.models.product import Product
    from src.features.telegram_bot.models.transaction_product import (
        TransactionProduct,
    )
    from sqlalchemy import select, func, desc, and_, text

    async with AsyncSessionLocal() as session:
        print("📊 КОМПЛЕКСНИЙ АНАЛІЗ ПРОДАЖІВ")
        print("=" * 60)
        print(f"📅 Дата звіту: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # 1. Загальна статистика
        print("🎯 ЗАГАЛЬНА СТАТИСТИКА:")
        print("-" * 60)

        # Загальні показники
        total_stats_query = (
            select(
                func.count_(func.distinct(Client.client_id)).label("total_clients"),
                func.count_(func.distinct(Spot.spot_id)).label("total_spots"),
                func.count_(func.distinct(Product.poster_product_id)).label(
                    "total_products"
                ),
                func.count_(Transaction.id).label("total_transactions"),
                func.sum(Transaction.sum).label("total_revenue"),
                func.avg(Transaction.sum).label("avg_check"),
                func.min(Transaction.date_close).label("first_transaction"),
                func.max(Transaction.date_close).label("last_transaction"),
            )
            .select_from(Transaction)
            .outerjoin(
                Client,
                Transaction.client == Client.client_id,
            )
            .outerjoin(Spot, Transaction.spot_id == Spot.spot_id)
            .outerjoin(
                TransactionProduct,
                Transaction.transaction_id == TransactionProduct.transaction_id,
            )
            .outerjoin(
                Product,
                TransactionProduct.poster_product_id == Product.poster_product_id,
            )
        )

        stats_result = await session.execute(total_stats_query)
        stats = stats_result.first()

        if stats:
            total_revenue = float(stats.total_revenue or 0)
            avg_check = float(stats.avg_check or 0)

            print(f"👥 Клієнтів в системі: {stats.total_clients or 0:,}")
            print(f"🏪 Точок продажу: {stats.total_spots or 0}")
            print(f"🛍️  Товарних позицій: {stats.total_products or 0:,}")
            print(f"📋 Всього транзакцій: {stats.total_transactions or 0:,}")
            print(f"💰 Загальний оборот: {total_revenue:,.2f} грн")
            print(f"💵 Середній чек: {avg_check:.2f} грн")

            if stats.first_transaction and stats.last_transaction:
                period = (stats.last_transaction - stats.first_transaction).days
                print(
                    f"📅 Період даних: {stats.first_transaction.strftime('%Y-%m-%d')} - {stats.last_transaction.strftime('%Y-%m-%d')} ({period} днів)"
                )

        # 2. Динаміка продажів по місяцях
        print("\n" + "=" * 60)
        print("📈 ДИНАМІКА ПРОДАЖІВ ПО МІСЯЦЯХ (останні 6 місяців):")
        print("-" * 60)

        six_months_ago = datetime.now() - timedelta(days=180)

        monthly_dynamics_query = (
            select(
                func.extract("year", Transaction.date_close).label("year"),
                func.extract("month", Transaction.date_close).label("month"),
                func.count(Transaction.id).label("transactions"),
                func.sum(Transaction.sum).label("revenue"),
                func.count(func.distinct(Transaction.client)).label("unique_clients"),
                func.avg(Transaction.sum).label("avg_check"),
            )
            .where(Transaction.date_close >= six_months_ago)
            .group_by(
                func.extract("year", Transaction.date_close),
                func.extract("month", Transaction.date_close),
            )
            .order_by("year", "month")
        )

        monthly_result = await session.execute(monthly_dynamics_query)
        monthly_data = monthly_result.all()

        print("Місяць      | Транзакцій | Оборот (грн) | Клієнтів | Серед. чек")
        print("-" * 65)

        for month_data in monthly_data:
            month_name = f"{int(month_data.year)}-{int(month_data.month):02d}"
            revenue = float(month_data.revenue or 0)
            avg_check = float(month_data.avg_check or 0)

            print(
                f"{month_name:11} | {month_data.transactions:>10,} | {revenue:>11,.0f} | {month_data.unique_clients:>7} | {avg_check:>9.2f}"
            )

        # 3. ТОП-5 по кожній категорії
        print("\n" + "=" * 60)
        print("🏆 ТОП-5 В КОЖНІЙ КАТЕГОРІЇ:")
        print("-" * 60)

        # ТОП-5 точок продажу
        print("🏪 ТОП-5 ТОЧОК ПРОДАЖУ:")
        top_spots_query = (
            select(
                Spot.name,
                func.count(Transaction.id).label("transactions"),
                func.sum(Transaction.sum).label("revenue"),
            )
            .select_from(Spot)
            .join(Transaction, Spot.spot_id == Transaction.spot_id)
            .group_by(Spot.name)
            .order_by(desc("revenue"))
            .limit(5)
        )

        spots_result = await session.execute(top_spots_query)
        top_spots = spots_result.all()

        for i, spot in enumerate(top_spots, 1):
            revenue = float(spot.revenue)
            print(
                f"   {i}. {spot.name}: {revenue:,.0f} грн ({spot.transactions:,} транз.)"
            )

        # ТОП-5 товарів
        print("\n🛍️  ТОП-5 ТОВАРІВ ЗА ОБОРОТОМ:")
        top_products_query = (
            select(
                Product.product_name,
                func.sum(TransactionProduct.sum).label("revenue"),
                func.sum(TransactionProduct.count).label("quantity"),
            )
            .select_from(Product)
            .join(
                TransactionProduct,
                Product.poster_product_id == TransactionProduct.poster_product_id,
            )
            .group_by(Product.product_name)
            .order_by(desc("revenue"))
            .limit(5)
        )

        products_result = await session.execute(top_products_query)
        top_products = products_result.all()

        for i, Product in enumerate(top_products, 1):
            revenue = float(Product.revenue)
            print(
                f"   {i}. {Product.product_name}: {revenue:,.0f} грн ({Product.quantity} шт)"
            )

        # ТОП-5 клієнтів
        print("\n👑 ТОП-5 VIP КЛІЄНТІВ:")
        top_clients_query = (
            select(
                Client.firstname,
                Client.lastname,
                Client.phone,
                func.sum(Transaction.sum).label("total_spent"),
                func.count(Transaction.id).label("transactions"),
            )
            .select_from(Client)
            .join(
                Transaction,
                Client.client_id == Transaction.client,
            )
            .group_by(
                Client.client_id,
                Client.firstname,
                Client.lastname,
                Client.phone,
            )
            .order_by(desc("total_spent"))
            .limit(5)
        )

        clients_result = await session.execute(top_clients_query)
        top_clients = clients_result.all()

        for i, client in enumerate(top_clients, 1):
            spent = float(client.total_spent)
            # Формуємо ім'я клієнта
            name = f"{client.firstname or ''} {client.lastname or ''}".strip()
            if not name:
                name = "Без імені"
            phone = client.phone or "Без телефону"
            print(
                f"   {i}. {name} ({phone}): {spent:,.0f} грн ({client.transactions} транз.)"
            )

        # 4. Аналіз ефективності
        print("\n" + "=" * 60)
        print("⚡ ПОКАЗНИКИ ЕФЕКТИВНОСТІ:")
        print("-" * 60)

        # Середня кількість покупок на клієнта
        if stats and stats.total_clients and stats.total_transactions:
            purchases_per_client = stats.total_transactions / stats.total_clients
            print(f"🔄 Середня к-ть покупок на клієнта: {purchases_per_client:.1f}")

        # Повторні покупки
        repeat_clients_query = select(func.count().label("repeat_clients")).select_from(
            select(Client.client_id)
            .select_from(Client)
            .join(
                Transaction,
                Client.client_id == Transaction.client,
            )
            .group_by(Client.client_id)
            .having(func.count(Transaction.id) > 1)
            .subquery()
        )

        repeat_result = await session.execute(repeat_clients_query)
        repeat_clients = repeat_result.scalar() or 0

        if stats and stats.total_clients:
            repeat_rate = (repeat_clients / stats.total_clients) * 100
            print(f"🔁 Відсоток клієнтів з повторними покупками: {repeat_rate:.1f}%")

        # Активність за останні 30 днів
        month_ago = datetime.now() - timedelta(days=30)

        recent_activity_query = select(
            func.count(Transaction.id).label("recent_transactions"),
            func.count(func.distinct(Transaction.client)).label("active_clients"),
        ).where(Transaction.date_close >= month_ago)

        recent_result = await session.execute(recent_activity_query)
        recent_stats = recent_result.first()

        if recent_stats:
            print(
                f"📅 Транзакцій за останні 30 днів: {recent_stats.recent_transactions or 0:,}"
            )
            print(
                f"👥 Активних клієнтів за останні 30 днів: {recent_stats.active_clients or 0}"
            )

        print("\n" + "=" * 60)
        print("✅ АНАЛІЗ ЗАВЕРШЕНО")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(comprehensive_sales_analysis())
