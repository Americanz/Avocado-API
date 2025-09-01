#!/usr/bin/env python3
"""
Аналіз клієнтів і їх покупок
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


async def analyze_clients_behavior():
    """Аналіз поведінки клієнтів"""
    from src.core.database.connection import AsyncSessionLocal
    from src.features.telegram_bot.models.client import Client
    from src.features.telegram_bot.models.transaction import Transaction
    from src.features.telegram_bot.models.spot import Spot
    from sqlalchemy import select, func, desc, and_, text

    async with AsyncSessionLocal() as session:
        print("👥 АНАЛІЗ КЛІЄНТІВ І ЇХ ПОКУПОК")
        print("=" * 60)

        # 1. ТОП-20 VIP клієнтів за сумою покупок
        print("💎 ТОП-20 VIP КЛІЄНТІВ ЗА СУМОЮ ПОКУПОК:")
        print("-" * 60)

        vip_clients_query = (
            select(
                Client.firstname,
                Client.lastname,
                Client.phone,
                Client.card_number,
                func.count(Transaction.id).label("total_transactions"),
                func.sum(Transaction.sum).label("total_spent"),
                func.avg(Transaction.sum).label("avg_transaction"),
                func.max(Transaction.sum).label("max_transaction"),
                func.min(Transaction.date_close).label("first_purchase"),
                func.max(Transaction.date_close).label("last_purchase"),
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
                Client.card_number,
            )
            .order_by(desc("total_spent"))
            .limit(20)
        )

        vip_result = await session.execute(vip_clients_query)
        vip_clients = vip_result.all()

        for i, client in enumerate(vip_clients, 1):
            total_spent = float(client.total_spent)
            avg_trans = float(client.avg_transaction)
            max_trans = float(client.max_transaction)

            # Формуємо ім'я клієнта
            client_name = f"{client.firstname or ''} {client.lastname or ''}".strip()
            if not client_name:
                client_name = "Без імені"

            # Обчислюємо період клієнта
            if client.first_purchase and client.last_purchase:
                period = (client.last_purchase - client.first_purchase).days
                period_text = f"{period} днів" if period > 0 else "новий клієнт"
            else:
                period_text = "н/д"

            print(f"{i:2d}. {client_name}")
            print(f"    📞 {client.phone or 'Без телефону'}")
            print(f"    🏷️  Картка: {client.card_number or 'Без картки'}")
            print(f"    💰 Витрачено: {total_spent:,.2f} грн")
            print(f"    📋 Транзакцій: {client.total_transactions}")
            print(f"    📊 Середній чек: {avg_trans:.2f} грн")
            print(f"    ⬆️  Максимальний чек: {max_trans:.2f} грн")
            print(f"    📅 Період: {period_text}")
            print()

        # 2. Аналіз по частоті покупок
        print("=" * 60)
        print("🔄 АНАЛІЗ ПО ЧАСТОТІ ПОКУПОК:")
        print("-" * 60)

        frequency_query = (
            select(
                func.count(Transaction.id).label("transaction_count"),
                func.count(func.distinct(Client.client_id)).label("client_count"),
            )
            .select_from(Client)
            .join(
                Transaction,
                Client.client_id == Transaction.client,
            )
            .group_by(Client.client_id)
            .subquery()
        )

        frequency_stats_query = (
            select(
                frequency_query.c.transaction_count,
                func.count().label("clients_with_this_frequency"),
            )
            .select_from(frequency_query)
            .group_by(frequency_query.c.transaction_count)
            .order_by(frequency_query.c.transaction_count)
        )

        freq_result = await session.execute(frequency_stats_query)
        frequency_data = freq_result.all()

        print("Кількість покупок | Кількість клієнтів")
        print("-" * 40)

        total_clients = 0
        for freq in frequency_data[:15]:  # Показуємо перші 15
            total_clients += freq.clients_with_this_frequency
            print(
                f"{freq.transaction_count:15d} | {freq.clients_with_this_frequency:16d}"
            )

        # Підраховуємо клієнтів з більше ніж 15 покупками
        many_purchases = sum(
            freq.clients_with_this_frequency for freq in frequency_data[15:]
        )
        if many_purchases > 0:
            print(f"{'15+':>15} | {many_purchases:16d}")

        print(f"\n📊 Всього активних клієнтів: {total_clients:,}")

        # 3. Сегментація клієнтів
        print("\n" + "=" * 60)
        print("🎯 СЕГМЕНТАЦІЯ КЛІЄНТІВ:")
        print("-" * 60)

        # VIP клієнти (більше 5000 грн)
        vip_count_query = (
            select(func.count(func.distinct(Client.client_id)).label("vip_count"))
            .select_from(Client)
            .join(
                Transaction,
                Client.client_id == Transaction.client,
            )
            .group_by(Client.client_id)
            .having(func.sum(Transaction.sum) >= 5000)
        )

        # Регулярні клієнти (5+ покупок)
        regular_count_query = (
            select(func.count(func.distinct(Client.client_id)).label("regular_count"))
            .select_from(Client)
            .join(
                Transaction,
                Client.client_id == Transaction.client,
            )
            .group_by(Client.client_id)
            .having(func.count(Transaction.id) >= 5)
        )

        # Нові клієнти (1-2 покупки)
        new_count_query = (
            select(func.count(func.distinct(Client.client_id)).label("new_count"))
            .select_from(Client)
            .join(
                Transaction,
                Client.client_id == Transaction.client,
            )
            .group_by(Client.client_id)
            .having(func.count(Transaction.id) <= 2)
        )

        # Виконуємо запити
        vip_result = await session.execute(
            select(func.count()).select_from(vip_count_query.subquery())
        )
        regular_result = await session.execute(
            select(func.count()).select_from(regular_count_query.subquery())
        )
        new_result = await session.execute(
            select(func.count()).select_from(new_count_query.subquery())
        )

        vip_count = vip_result.scalar() or 0
        regular_count = regular_result.scalar() or 0
        new_count = new_result.scalar() or 0

        print(f"💎 VIP клієнти (>5000 грн): {vip_count}")
        print(f"🔄 Регулярні клієнти (5+ покупок): {regular_count}")
        print(f"🆕 Нові клієнти (1-2 покупки): {new_count}")

        # 4. Аналіз по точкам продажу для клієнтів
        print("\n" + "=" * 60)
        print("🏪 УЛЮБЛЕНІ ТОЧКИ ПРОДАЖУ КЛІЄНТІВ:")
        print("-" * 60)

        spot_preference_query = (
            select(
                Spot.name.label("spot_name"),
                func.count(func.distinct(Client.client_id)).label("unique_clients"),
                func.count(Transaction.id).label("total_transactions"),
                func.avg(Transaction.sum).label("avg_check"),
            )
            .select_from(Spot)
            .join(Transaction, Spot.spot_id == Transaction.spot_id)
            .join(
                Client,
                Transaction.client == Client.client_id,
            )
            .group_by(Spot.name)
            .order_by(desc("unique_clients"))
        )

        spot_pref_result = await session.execute(spot_preference_query)
        spot_preferences = spot_pref_result.all()

        for i, spot in enumerate(spot_preferences, 1):
            avg_check = float(spot.avg_check)

            print(f"{i:2d}. {spot.spot_name}")
            print(f"    👥 Унікальних клієнтів: {spot.unique_clients}")
            print(f"    📋 Транзакцій: {spot.total_transactions}")
            print(f"    💰 Середній чек: {avg_check:.2f} грн")
            print()

        # 5. Аналіз активності за останній місяць
        print("=" * 60)
        print("📅 АКТИВНІСТЬ ЗА ОСТАННІЙ МІСЯЦЬ:")
        print("-" * 60)

        month_ago = datetime.now() - timedelta(days=30)

        monthly_activity_query = (
            select(
                func.count(func.distinct(Client.client_id)).label("active_clients"),
                func.count(Transaction.id).label("transactions"),
                func.sum(Transaction.sum).label("revenue"),
                func.avg(Transaction.sum).label("avg_check"),
            )
            .select_from(Client)
            .join(
                Transaction,
                Client.client_id == Transaction.client,
            )
            .where(Transaction.date_close >= month_ago)
        )

        monthly_result = await session.execute(monthly_activity_query)
        monthly_stats = monthly_result.first()

        if monthly_stats:
            revenue = float(monthly_stats.revenue or 0)
            avg_check = float(monthly_stats.avg_check or 0)

            print(f"👥 Активних клієнтів: {monthly_stats.active_clients or 0}")
            print(f"📋 Транзакцій: {monthly_stats.transactions or 0}")
            print(f"💰 Оборот: {revenue:,.2f} грн")
            print(f"💵 Середній чек: {avg_check:.2f} грн")


if __name__ == "__main__":
    asyncio.run(analyze_clients_behavior())
