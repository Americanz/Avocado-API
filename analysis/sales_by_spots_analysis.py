#!/usr/bin/env python3
"""
Аналіз продажів по точках продажу (spots)
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


async def analyze_sales_by_spots():
    """Аналіз продажів по точках продажу"""
    from src.core.database.connection import AsyncSessionLocal
    from src.features.telegram_bot.models.spot import Spot
    from src.features.telegram_bot.models.transaction import Transaction
    from sqlalchemy import select, func, desc

    async with AsyncSessionLocal() as session:
        print("🏪 АНАЛІЗ ПРОДАЖІВ ПО ТОЧКАХ ПРОДАЖУ")
        print("=" * 60)

        # 1. Загальна статистика по точках
        query = (
            select(
                Spot.spot_id,
                Spot.name,
                Spot.address,
                func.count(Transaction.id).label("total_transactions"),
                func.sum(Transaction.sum).label("total_revenue"),
                func.avg(Transaction.sum).label("avg_transaction"),
                func.max(Transaction.sum).label("max_transaction"),
                func.min(Transaction.sum).label("min_transaction"),
            )
            .select_from(Spot)
            .outerjoin(Transaction, Spot.spot_id == Transaction.spot_id)
            .group_by(Spot.spot_id, Spot.name, Spot.address)
            .order_by(desc("total_revenue"))
        )

        result = await session.execute(query)
        spots_stats = result.all()

        print("📊 ТОП ТОЧОК ПО ЗАГАЛЬНОМУ ОБОРОТУ:")
        print("-" * 60)

        total_revenue = 0
        total_transactions = 0

        for i, spot in enumerate(spots_stats, 1):
            revenue = float(spot.total_revenue or 0)
            transactions = spot.total_transactions or 0
            avg_trans = float(spot.avg_transaction or 0)

            total_revenue += revenue
            total_transactions += transactions

            print(f"{i:2d}. {spot.name}")
            print(f"    📍 {spot.address}")
            print(f"    💰 Оборот: {revenue:,.2f} грн")
            print(f"    📋 Транзакцій: {transactions:,}")
            print(f"    📊 Середній чек: {avg_trans:.2f} грн")
            if spot.max_transaction:
                print(f"    ⬆️  Макс чек: {float(spot.max_transaction):.2f} грн")
            print()

        print("=" * 60)
        print(f"🎯 ЗАГАЛЬНІ ПІДСУМКИ:")
        print(f"   💰 Загальний оборот: {total_revenue:,.2f} грн")
        print(f"   📋 Всього транзакцій: {total_transactions:,}")
        print(f"   📊 Середній чек: {total_revenue/total_transactions:.2f} грн")
        print()

        # 2. Аналіз по місяцях
        print("📅 АНАЛІЗ ПО ОСТАННІХ 3 МІСЯЦЯХ:")
        print("-" * 60)

        # Останні 3 місяці
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)

        monthly_query = (
            select(
                Spot.name,
                func.extract("year", Transaction.date_close).label("year"),
                func.extract("month", Transaction.date_close).label("month"),
                func.count(Transaction.id).label("transactions"),
                func.sum(Transaction.sum).label("revenue"),
            )
            .select_from(Spot)
            .join(Transaction, Spot.spot_id == Transaction.spot_id)
            .where(Transaction.date_close >= start_date)
            .group_by(
                Spot.name,
                func.extract("year", Transaction.date_close),
                func.extract("month", Transaction.date_close),
            )
            .order_by("year", "month", desc("revenue"))
        )

        monthly_result = await session.execute(monthly_query)
        monthly_data = monthly_result.all()

        current_month = None
        for row in monthly_data:
            month_year = f"{int(row.year)}-{int(row.month):02d}"

            if month_year != current_month:
                if current_month is not None:
                    print()
                print(f"📅 {month_year}:")
                current_month = month_year

            print(
                f"   {row.name}: {float(row.revenue):,.0f} грн ({row.transactions} транз.)"
            )

        # 3. Топ-5 найактивніших точок за останній тиждень
        print("\n" + "=" * 60)
        print("🔥 ТОП-5 НАЙАКТИВНІШИХ ТОЧОК ЗА ОСТАННІЙ ТИЖДЕНЬ:")
        print("-" * 60)

        week_ago = datetime.now() - timedelta(days=7)

        weekly_query = (
            select(
                Spot.name,
                func.count(Transaction.id).label("transactions"),
                func.sum(Transaction.sum).label("revenue"),
            )
            .select_from(Spot)
            .join(Transaction, Spot.spot_id == Transaction.spot_id)
            .where(Transaction.date_close >= week_ago)
            .group_by(Spot.name)
            .order_by(desc("transactions"))
            .limit(5)
        )

        weekly_result = await session.execute(weekly_query)
        weekly_top = weekly_result.all()

        for i, spot in enumerate(weekly_top, 1):
            print(f"{i}. {spot.name}")
            print(f"   📋 {spot.transactions} транзакцій")
            print(f"   💰 {float(spot.revenue):,.0f} грн")
            print()


if __name__ == "__main__":
    asyncio.run(analyze_sales_by_spots())
