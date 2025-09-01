#!/usr/bin/env python3
"""
Аналіз трендів і прогнозів продажів
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


async def analyze_sales_trends():
    """Аналіз трендів продажів"""
    from src.core.database.connection import AsyncSessionLocal
    from src.features.telegram_bot.models.spot import Spot
    from src.features.telegram_bot.models.transaction import Transaction
    from src.features.telegram_bot.models.client import Client
    from sqlalchemy import select, func, desc, and_, text

    async with AsyncSessionLocal() as session:
        print("📈 АНАЛІЗ ТРЕНДІВ ПРОДАЖІВ")
        print("=" * 60)

        # 1. Тренди по днях тижня
        print("📅 АНАЛІЗ ПО ДНЯХ ТИЖНЯ:")
        print("-" * 60)

        # PostgreSQL: 1=Понеділок, 7=Неділя
        weekday_query = (
            select(
                func.extract("dow", Transaction.date_close).label("day_of_week"),
                func.count(Transaction.id).label("transactions"),
                func.sum(Transaction.sum).label("revenue"),
                func.avg(Transaction.sum).label("avg_check"),
                func.count(func.distinct(Transaction.client)).label("unique_clients"),
            )
            .group_by(func.extract("dow", Transaction.date_close))
            .order_by("day_of_week")
        )

        weekday_result = await session.execute(weekday_query)
        weekday_data = weekday_result.all()

        weekdays = [
            "Неділя",
            "Понеділок",
            "Вівторок",
            "Середа",
            "Четвер",
            "П'ятниця",
            "Субота",
        ]

        print("День тижня   | Транзакцій | Оборот (грн) | Серед. чек | Клієнтів")
        print("-" * 70)

        total_week_revenue = 0
        total_week_transactions = 0

        for day_data in weekday_data:
            day_num = int(day_data.day_of_week)
            day_name = weekdays[day_num]
            revenue = float(day_data.revenue or 0)
            avg_check = float(day_data.avg_check or 0)

            total_week_revenue += revenue
            total_week_transactions += day_data.transactions

            print(
                f"{day_name:12} | {day_data.transactions:>10,} | {revenue:>11,.0f} | {avg_check:>9.2f} | {day_data.unique_clients:>7}"
            )

        # Знаходимо найкращий і найгірший дні
        best_day = max(weekday_data, key=lambda x: float(x.revenue or 0))
        worst_day = min(weekday_data, key=lambda x: float(x.revenue or 0))

        print(
            f"\n🏆 Найкращий день: {weekdays[int(best_day.day_of_week)]} ({float(best_day.revenue):,.0f} грн)"
        )
        print(
            f"📉 Найгірший день: {weekdays[int(worst_day.day_of_week)]} ({float(worst_day.revenue):,.0f} грн)"
        )

        # 2. Тренди по годинах
        print("\n" + "=" * 60)
        print("🕐 АНАЛІЗ ПО ГОДИНАХ ДНЯ:")
        print("-" * 60)

        hourly_query = (
            select(
                func.extract("hour", Transaction.date_close).label("hour"),
                func.count(Transaction.id).label("transactions"),
                func.sum(Transaction.sum).label("revenue"),
                func.avg(Transaction.sum).label("avg_check"),
            )
            .group_by(func.extract("hour", Transaction.date_close))
            .order_by("hour")
        )

        hourly_result = await session.execute(hourly_query)
        hourly_data = hourly_result.all()

        print("Година | Транзакцій | Оборот (грн) | Серед. чек")
        print("-" * 50)

        peak_hours = []
        for hour_data in hourly_data:
            hour = int(hour_data.hour)
            revenue = float(hour_data.revenue or 0)
            avg_check = float(hour_data.avg_check or 0)

            # Визначаємо пікові години (більше середнього)
            if (
                hour_data.transactions
                > total_week_transactions / len(weekday_data) / 24
            ):
                peak_hours.append(hour)

            print(
                f"{hour:2d}:00 | {hour_data.transactions:>10,} | {revenue:>11,.0f} | {avg_check:>9.2f}"
            )

        print(f"\n⚡ Пікові години: {', '.join(f'{h}:00' for h in peak_hours)}")

        # 3. Місячна динаміка
        print("\n" + "=" * 60)
        print("📊 МІСЯЧНА ДИНАМІКА (останні 12 місяців):")
        print("-" * 60)

        year_ago = datetime.now() - timedelta(days=365)

        monthly_trend_query = (
            select(
                func.extract("year", Transaction.date_close).label("year"),
                func.extract("month", Transaction.date_close).label("month"),
                func.count(Transaction.id).label("transactions"),
                func.sum(Transaction.sum).label("revenue"),
                func.count(func.distinct(Transaction.client)).label("unique_clients"),
                func.avg(Transaction.sum).label("avg_check"),
            )
            .where(Transaction.date_close >= year_ago)
            .group_by(
                func.extract("year", Transaction.date_close),
                func.extract("month", Transaction.date_close),
            )
            .order_by("year", "month")
        )

        monthly_result = await session.execute(monthly_trend_query)
        monthly_trend = monthly_result.all()

        print("Місяць      | Транзакцій | Оборот (грн) | Ріст обороту | Клієнтів")
        print("-" * 70)

        prev_revenue = None
        for month_data in monthly_trend:
            month_name = f"{int(month_data.year)}-{int(month_data.month):02d}"
            revenue = float(month_data.revenue or 0)

            # Розраховуємо ріст
            if prev_revenue is not None and prev_revenue > 0:
                growth = ((revenue - prev_revenue) / prev_revenue) * 100
                growth_str = f"{growth:+.1f}%"
            else:
                growth_str = "н/д"

            print(
                f"{month_name:11} | {month_data.transactions:>10,} | {revenue:>11,.0f} | {growth_str:>11} | {month_data.unique_clients:>7}"
            )
            prev_revenue = revenue

        # 4. Сезонність
        print("\n" + "=" * 60)
        print("🌟 АНАЛІЗ СЕЗОННОСТІ:")
        print("-" * 60)

        seasonal_query = (
            select(
                func.extract("month", Transaction.date_close).label("month"),
                func.count(Transaction.id).label("transactions"),
                func.sum(Transaction.sum).label("revenue"),
                func.avg(Transaction.sum).label("avg_check"),
            )
            .group_by(func.extract("month", Transaction.date_close))
            .order_by("month")
        )

        seasonal_result = await session.execute(seasonal_query)
        seasonal_data = seasonal_result.all()

        months = [
            "Січень",
            "Лютий",
            "Березень",
            "Квітень",
            "Травень",
            "Червень",
            "Липень",
            "Серпень",
            "Вересень",
            "Жовтень",
            "Листопад",
            "Грудень",
        ]

        print("Місяць     | Транзакцій | Оборот (грн) | Серед. чек")
        print("-" * 55)

        seasonal_revenues = []
        for month_data in seasonal_data:
            month_num = int(month_data.month) - 1
            month_name = months[month_num]
            revenue = float(month_data.revenue or 0)
            avg_check = float(month_data.avg_check or 0)
            seasonal_revenues.append((month_name, revenue))

            print(
                f"{month_name:10} | {month_data.transactions:>10,} | {revenue:>11,.0f} | {avg_check:>9.2f}"
            )

        # Знаходимо найкращий і найгірший місяці
        if seasonal_revenues:
            best_month = max(seasonal_revenues, key=lambda x: x[1])
            worst_month = min(seasonal_revenues, key=lambda x: x[1])

            print(f"\n🏆 Найкращий місяць: {best_month[0]} ({best_month[1]:,.0f} грн)")
            print(f"📉 Найгірший місяць: {worst_month[0]} ({worst_month[1]:,.0f} грн)")

        # 5. Прогноз на наступний місяць
        print("\n" + "=" * 60)
        print("🔮 ПРОСТИЙ ПРОГНОЗ НА НАСТУПНИЙ МІСЯЦЬ:")
        print("-" * 60)

        # Беремо останні 3 місяці для прогнозу
        recent_months = monthly_trend[-3:] if len(monthly_trend) >= 3 else monthly_trend

        if len(recent_months) >= 2:
            # Розраховуємо середній ріст
            growths = []
            for i in range(1, len(recent_months)):
                prev_rev = float(recent_months[i - 1].revenue or 0)
                curr_rev = float(recent_months[i].revenue or 0)
                if prev_rev > 0:
                    growth = (curr_rev - prev_rev) / prev_rev
                    growths.append(growth)

            if growths:
                avg_growth = sum(growths) / len(growths)
                last_month_revenue = float(recent_months[-1].revenue or 0)
                predicted_revenue = last_month_revenue * (1 + avg_growth)

                print(f"📊 Останній місяць: {last_month_revenue:,.0f} грн")
                print(f"📈 Середній ріст: {avg_growth*100:+.1f}%")
                print(f"🎯 Прогноз на наступний місяць: {predicted_revenue:,.0f} грн")

                # Рекомендації
                if avg_growth > 0.05:  # 5% ріст
                    print("✅ Тренд: Позитивний ріст")
                elif avg_growth < -0.05:  # 5% спад
                    print("⚠️  Тренд: Негативний, потрібні заходи")
                else:
                    print("➡️  Тренд: Стабільний")


if __name__ == "__main__":
    asyncio.run(analyze_sales_trends())
