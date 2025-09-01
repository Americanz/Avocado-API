#!/usr/bin/env python3
"""
Головний скрипт для запуску всіх аналізів продажів з HTML звітністю
"""

import asyncio
import sys
import os
import webbrowser
from datetime import datetime
from typing import Dict, Any

# Додаємо корневу папку до шляху
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from analysis.html_report_generator import HTMLReportGenerator


class AnalysisCollector:
    """Збирач результатів аналізу для HTML звіту"""

    def __init__(self):
        self.results = {
            "main_stats": {},
            "spots_analysis": [],
            "top_products": [],
            "clients_analysis": {},
            "trends_analysis": [],
            "bonus_analysis": {},
            "sales_trends": [],
            "comprehensive_stats": {},
            "detailed_product_analysis": [],
            "recommendations": [],
        }

    def collect_main_stats(self):
        """Збирає основні статистики"""
        # Тут буде логіка збору основних показників
        from src.core.database.connection import SessionLocal
        from src.features.telegram_bot.models import Transaction
        from sqlalchemy import func

        with SessionLocal() as db:
            # Загальний дохід
            total_revenue = db.query(func.sum(Transaction.sum)).scalar() or 0

            # Кількість транзакцій
            total_transactions = db.query(func.count(Transaction.id)).scalar() or 0

            # Середній чек
            avg_check = db.query(func.avg(Transaction.sum)).scalar() or 0

            # Унікальні клієнти
            unique_clients = (
                db.query(func.count(func.distinct(Transaction.client_id))).scalar() or 0
            )

            self.results["main_stats"] = {
                "total_revenue": f"{total_revenue:,.2f} грн",
                "total_transactions": f"{total_transactions:,}",
                "avg_check": f"{avg_check:.2f} грн",
                "unique_clients": f"{unique_clients:,}",
            }

    def collect_spots_analysis(self):
        """Збирає аналіз по точках"""
        from src.core.database.connection import SessionLocal
        from src.features.telegram_bot.models import Transaction, Spot
        from sqlalchemy import func

        with SessionLocal() as db:
            spots_data = (
                db.query(
                    Spot.name,
                    func.sum(Transaction.sum).label("revenue"),
                    func.count(Transaction.id).label("transactions"),
                    func.avg(Transaction.sum).label("avg_check"),
                )
                .join(Transaction, Spot.spot_id == Transaction.spot_id)
                .group_by(Spot.name)
                .all()
            )

            total_revenue = sum(spot.revenue for spot in spots_data)

            self.results["spots_analysis"] = [
                {
                    "name": spot.name,
                    "revenue": f"{spot.revenue:,.2f}",
                    "transactions": spot.transactions,
                    "avg_check": f"{spot.avg_check:.2f}",
                    "revenue_percent": round(
                        (
                            (spot.revenue / total_revenue * 100)
                            if total_revenue > 0
                            else 0
                        ),
                        1,
                    ),
                }
                for spot in spots_data
            ]

    def collect_products_analysis(self):
        """Збирає аналіз топ продуктів"""
        from src.core.database.connection import SessionLocal
        from src.features.telegram_bot.models import TransactionProduct, Product
        from sqlalchemy import func

        with SessionLocal() as db:
            products_data = (
                db.query(
                    Product.product_name,
                    func.sum(TransactionProduct.sum).label("sales"),
                    func.sum(TransactionProduct.count).label("quantity"),
                )
                .join(
                    TransactionProduct,
                    Product.poster_product_id == TransactionProduct.poster_product_id,
                )
                .group_by(Product.product_name)
                .order_by(func.sum(TransactionProduct.sum).desc())
                .limit(10)
                .all()
            )

            total_sales = sum(product.sales for product in products_data)

            self.results["top_products"] = [
                {
                    "name": product.product_name or "Невідомий продукт",
                    "sales": f"{product.sales:,.2f}",
                    "quantity": f"{product.quantity:,.0f}",
                    "percentage": round(
                        (product.sales / total_sales * 100) if total_sales > 0 else 0, 1
                    ),
                }
                for product in products_data
            ]

    def collect_clients_analysis(self):
        """Збирає аналіз клієнтів"""
        from src.core.database.connection import SessionLocal
        from src.features.telegram_bot.models import Transaction, Client
        from sqlalchemy import func

        with SessionLocal() as db:
            # Топ клієнти
            top_clients = (
                db.query(
                    func.concat(Client.firstname, " ", Client.lastname).label("name"),
                    func.sum(Transaction.sum).label("spent"),
                    func.count(Transaction.id).label("transactions"),
                    func.avg(Transaction.sum).label("avg_check"),
                )
                .join(Transaction, Client.client_id == Transaction.client_id)
                .group_by(Client.client_id, Client.firstname, Client.lastname)
                .order_by(func.sum(Transaction.sum).desc())
                .limit(10)
                .all()
            )

            # Загальна кількість клієнтів
            total_clients = (
                db.query(func.count(func.distinct(Transaction.client_id))).scalar() or 0
            )

            # Середня кількість покупок на клієнта
            # Спочатку отримуємо кількість транзакцій для кожного клієнта
            client_transactions = (
                db.query(func.count(Transaction.id).label("transaction_count"))
                .group_by(Transaction.client_id)
                .subquery()
            )

            # Тепер рахуємо середнє
            avg_transactions_per_client = (
                db.query(func.avg(client_transactions.c.transaction_count)).scalar()
                or 0
            )

            self.results["clients_analysis"] = {
                "insights": [
                    f"Загальна кількість клієнтів: {total_clients:,}",
                    f"Середня кількість покупок на клієнта: {avg_transactions_per_client:.1f}",
                    f"Топ 10 клієнтів генерують {sum(client.spent for client in top_clients):,.2f} грн доходу",
                ],
                "top_clients": [
                    {
                        "name": client.name or "Невідомий клієнт",
                        "spent": f"{client.spent:,.2f}",
                        "transactions": client.transactions,
                        "avg_check": f"{client.avg_check:.2f}",
                    }
                    for client in top_clients
                ],
            }

    def collect_bonus_analysis(self):
        """Збирає аналіз бонусної системи"""
        from src.core.database.connection import SessionLocal
        from src.features.telegram_bot.models import Transaction
        from sqlalchemy import func

        with SessionLocal() as db:
            # Кількість транзакцій з бонусами
            transactions_with_bonus = (
                db.query(func.count(Transaction.id))
                .filter(Transaction.bonus > 0)
                .scalar()
                or 0
            )

            # Середній відсоток бонусу
            avg_bonus_percent = (
                db.query(func.avg(Transaction.bonus))
                .filter(Transaction.bonus > 0)
                .scalar()
                or 0
            )

            # Максимальний відсоток бонусу
            max_bonus_percent = db.query(func.max(Transaction.bonus)).scalar() or 0

            # Загальна сума бонусів (розрахована як відсоток від суми)
            # bonus - це відсоток, тому: сума_бонусу = сума_транзакції * (bonus / 100)
            total_bonus_amount = (
                db.query(func.sum(Transaction.sum * Transaction.bonus / 100))
                .filter(Transaction.bonus > 0)
                .scalar()
                or 0
            )

            # Середня сума бонусу за транзакцію
            avg_bonus_amount = (
                db.query(func.avg(Transaction.sum * Transaction.bonus / 100))
                .filter(Transaction.bonus > 0)
                .scalar()
                or 0
            )

            # Максимальна сума бонусу за одну транзакцію
            max_bonus_amount = (
                db.query(func.max(Transaction.sum * Transaction.bonus / 100))
                .filter(Transaction.bonus > 0)
                .scalar()
                or 0
            )

            # Відсоток транзакцій з бонусами
            total_transactions = db.query(func.count(Transaction.id)).scalar() or 1
            bonus_transaction_percentage = (
                (transactions_with_bonus / total_transactions * 100)
                if total_transactions > 0
                else 0
            )

            # Середня сума транзакцій з бонусами
            avg_transaction_with_bonus = (
                db.query(func.avg(Transaction.sum))
                .filter(Transaction.bonus > 0)
                .scalar()
                or 0
            )

            self.results["bonus_analysis"] = {
                "total_bonus_amount": f"{total_bonus_amount:,.2f} грн",
                "transactions_with_bonus": f"{transactions_with_bonus:,}",
                "avg_bonus_percent": f"{avg_bonus_percent:.2f}%",
                "max_bonus_percent": f"{max_bonus_percent:.2f}%",
                "avg_bonus_amount": f"{avg_bonus_amount:.2f} грн",
                "max_bonus_amount": f"{max_bonus_amount:.2f} грн",
                "bonus_transaction_percentage": f"{bonus_transaction_percentage:.1f}%",
                "avg_transaction_with_bonus": f"{avg_transaction_with_bonus:.2f} грн",
                "insights": [
                    f"Загальна сума нарахованих бонусів: {total_bonus_amount:,.2f} грн",
                    f"Бонуси отримали {transactions_with_bonus:,} транзакцій ({bonus_transaction_percentage:.1f}%)",
                    f"Середній відсоток бонусу: {avg_bonus_percent:.2f}% від суми покупки",
                    f"Середня сума бонусу за транзакцію: {avg_bonus_amount:.2f} грн",
                    f"Максимальний бонус за транзакцію: {max_bonus_amount:.2f} грн (при {max_bonus_percent:.2f}%)",
                    f"Середня сума транзакцій з бонусами: {avg_transaction_with_bonus:.2f} грн",
                ],
            }

    def collect_sales_trends_analysis(self):
        """Збирає аналіз трендів продажів по місяцях"""
        from src.core.database.connection import SessionLocal
        from src.features.telegram_bot.models import Transaction
        from sqlalchemy import func, extract

        with SessionLocal() as db:
            # Продажі по місяцях
            monthly_sales = (
                db.query(
                    extract("year", Transaction.date_close).label("year"),
                    extract("month", Transaction.date_close).label("month"),
                    func.sum(Transaction.sum).label("revenue"),
                    func.count(Transaction.id).label("transactions"),
                    func.avg(Transaction.sum).label("avg_check"),
                )
                .filter(Transaction.date_close.isnot(None))
                .group_by(
                    extract("year", Transaction.date_close),
                    extract("month", Transaction.date_close),
                )
                .order_by(
                    extract("year", Transaction.date_close),
                    extract("month", Transaction.date_close),
                )
                .all()
            )

            self.results["sales_trends"] = [
                {
                    "period": f"{int(row.year)}-{int(row.month):02d}",
                    "revenue": f"{row.revenue:,.2f}",
                    "transactions": f"{row.transactions:,}",
                    "avg_check": f"{row.avg_check:.2f}",
                    "month_name": self._get_month_name(int(row.month)),
                }
                for row in monthly_sales
            ]

    def collect_comprehensive_stats(self):
        """Збирає комплексну статистику"""
        from src.core.database.connection import SessionLocal
        from src.features.telegram_bot.models import (
            Transaction,
            TransactionProduct,
            Product,
            Spot,
        )
        from sqlalchemy import func

        with SessionLocal() as db:
            # Загальна кількість продуктів
            total_products = (
                db.query(func.count(func.distinct(Product.poster_product_id))).scalar()
                or 0
            )

            # Загальна кількість точок
            total_spots = (
                db.query(func.count(func.distinct(Spot.spot_id))).scalar() or 0
            )

            # Найбільша транзакція
            max_transaction = db.query(func.max(Transaction.sum)).scalar() or 0

            # Найменша транзакція (більше 0)
            min_transaction = (
                db.query(func.min(Transaction.sum)).filter(Transaction.sum > 0).scalar()
                or 0
            )

            # Середня кількість товарів в чеку
            # Спочатку отримуємо кількість товарів для кожної транзакції
            products_per_transaction = (
                db.query(func.count(TransactionProduct.id).label("product_count"))
                .group_by(TransactionProduct.transaction_id)
                .subquery()
            )

            # Тепер рахуємо середнє
            avg_products_per_transaction = (
                db.query(func.avg(products_per_transaction.c.product_count)).scalar()
                or 0
            )

            self.results["comprehensive_stats"] = {
                "total_products": f"{total_products:,}",
                "total_spots": f"{total_spots:,}",
                "max_transaction": f"{max_transaction:,.2f} грн",
                "min_transaction": f"{min_transaction:.2f} грн",
                "avg_products_per_transaction": f"{avg_products_per_transaction:.1f}",
                "insights": [
                    f"У системі зареєстровано {total_products:,} унікальних продуктів",
                    f"Працює {total_spots:,} точок продажу",
                    f"Найбільша транзакція: {max_transaction:,.2f} грн",
                    f"Найменша транзакція: {min_transaction:.2f} грн",
                    f"У середньому {avg_products_per_transaction:.1f} товарів в чеку",
                ],
            }

    def collect_detailed_product_analysis(self):
        """Збирає детальний аналіз продуктів по категоріях"""
        from src.core.database.connection import SessionLocal
        from src.features.telegram_bot.models import TransactionProduct, Product
        from sqlalchemy import func

        with SessionLocal() as db:
            # Аналіз по категоріях
            category_analysis = (
                db.query(
                    Product.category_name,
                    func.sum(TransactionProduct.sum).label("sales"),
                    func.sum(TransactionProduct.count).label("quantity"),
                    func.count(func.distinct(Product.poster_product_id)).label(
                        "unique_products"
                    ),
                )
                .join(
                    TransactionProduct,
                    Product.poster_product_id == TransactionProduct.poster_product_id,
                )
                .filter(Product.category_name.isnot(None))
                .group_by(Product.category_name)
                .order_by(func.sum(TransactionProduct.sum).desc())
                .limit(15)
                .all()
            )

            total_category_sales = sum(cat.sales for cat in category_analysis)

            self.results["detailed_product_analysis"] = [
                {
                    "category": cat.category_name or "Інша категорія",
                    "sales": f"{cat.sales:,.2f}",
                    "quantity": f"{cat.quantity:,.0f}",
                    "unique_products": f"{cat.unique_products:,}",
                    "percentage": round(
                        (
                            (cat.sales / total_category_sales * 100)
                            if total_category_sales > 0
                            else 0
                        ),
                        1,
                    ),
                }
                for cat in category_analysis
            ]

    def _get_month_name(self, month_num):
        """Повертає назву місяця українською"""
        months = {
            1: "Січень",
            2: "Лютий",
            3: "Березень",
            4: "Квітень",
            5: "Травень",
            6: "Червень",
            7: "Липень",
            8: "Серпень",
            9: "Вересень",
            10: "Жовтень",
            11: "Листопад",
            12: "Грудень",
        }
        return months.get(month_num, f"Місяць {month_num}")

    def add_recommendations(self):
        """Додає рекомендації на основі аналізу"""
        self.results["recommendations"] = [
            {
                "title": "🎯 Фокус на топ продуктах",
                "description": "Збільшити промо активність для найпопулярніших товарів",
            },
            {
                "title": "👥 Програма лояльності",
                "description": "Розробити спеціальні пропозиції для топ клієнтів",
            },
            {
                "title": "📊 Оптимізація точок",
                "description": "Проаналізувати ефективність менш прибуткових точок",
            },
            {
                "title": "🚀 Автоматизація",
                "description": "Впровадити автоматичні звіти для моніторингу трендів",
            },
        ]


async def run_all_analysis_with_html():
    """Запуск всіх аналізів з генерацією HTML звіту"""

    print("🚀 ЗАПУСК ПОВНОГО АНАЛІЗУ ПРОДАЖІВ З HTML ЗВІТНІСТЮ")
    print("=" * 80)
    print(f"⏰ Початок: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    try:
        # Ініціалізуємо збирач результатів
        collector = AnalysisCollector()

        # Збираємо всі дані
        print("\n📊 Збір основних статистик...")
        collector.collect_main_stats()

        print("🏪 Аналіз по точках продажу...")
        collector.collect_spots_analysis()

        print("🛍️ Аналіз топ продуктів...")
        collector.collect_products_analysis()

        print("👥 Аналіз клієнтів...")
        collector.collect_clients_analysis()

        print("🎁 Аналіз бонусної системи...")
        collector.collect_bonus_analysis()

        print("📈 Аналіз трендів продажів...")
        collector.collect_sales_trends_analysis()

        print("📋 Комплексна статистика...")
        collector.collect_comprehensive_stats()

        print("🏷️ Детальний аналіз продуктів по категоріях...")
        collector.collect_detailed_product_analysis()

        print("💡 Генерація рекомендацій...")
        collector.add_recommendations()

        # Налагодження: показуємо зібрані дані
        print("\n🔍 НАЛАГОДЖЕННЯ - Зібрані дані:")
        for key, value in collector.results.items():
            if isinstance(value, list):
                print(f"  {key}: {len(value)} елементів")
            elif isinstance(value, dict):
                print(f"  {key}: {len(value)} ключів")
            else:
                print(f"  {key}: {type(value)}")

        # Генеруємо HTML звіт
        print("\n🎨 Створення HTML звіту...")
        generator = HTMLReportGenerator()
        html_file = generator.create_main_report(collector.results)

        print("\n" + "=" * 80)
        print("✅ АНАЛІЗ ЗАВЕРШЕНО УСПІШНО!")
        print(f"📄 HTML звіт створено: {html_file}")
        print(f"⏰ Завершено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # Відкриваємо звіт в браузері
        try:
            print("\n🌐 Відкриття звіту в браузері...")
            webbrowser.open(f"file://{os.path.abspath(html_file)}")
            print("✅ Звіт відкрито в браузері!")
        except Exception as e:
            print(f"⚠️ Не вдалося автоматично відкрити браузер: {e}")
            print(f"💡 Відкрийте файл вручну: {os.path.abspath(html_file)}")

    except Exception as e:
        print(f"❌ Помилка при виконанні аналізу: {e}")
        import traceback

        traceback.print_exc()


async def run_legacy_analysis():
    """Запуск оригінальних аналізів (legacy mode)"""

    print("🚀 ЗАПУСК ПОВНОГО АНАЛІЗУ ПРОДАЖІВ (LEGACY MODE)")
    print("=" * 80)
    print(f"⏰ Початок: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Імпортуємо всі аналізи
    try:
        from analysis.comprehensive_sales_analysis import comprehensive_sales_analysis
        from analysis.sales_by_spots_analysis import analyze_sales_by_spots
        from analysis.products_sales_analysis import analyze_products_sales
        from analysis.clients_behavior_analysis import analyze_clients_behavior
        from analysis.sales_trends_analysis import analyze_sales_trends

        # 1. Комплексний аналіз (загальний огляд)
        print("\n🎯 1/6: ЗАГАЛЬНИЙ ОГЛЯД")
        print("-" * 40)
        await comprehensive_sales_analysis()

        # 2. Аналіз по точках продажу
        print("\n🏪 2/6: АНАЛІЗ ПО ТОЧКАХ ПРОДАЖУ")
        print("-" * 40)
        await analyze_sales_by_spots()

        # 3. Аналіз по товарах
        print("\n🛍️  3/6: АНАЛІЗ ПО ТОВАРАХ")
        print("-" * 40)
        await analyze_products_sales()

        # 4. Аналіз клієнтів
        print("\n👥 4/6: АНАЛІЗ КЛІЄНТІВ")
        print("-" * 40)
        await analyze_clients_behavior()

        # 5. Аналіз трендів
        print("\n📈 5/6: АНАЛІЗ ТРЕНДІВ")
        print("-" * 40)
        await analyze_sales_trends()

        # 6. Додаткові аналізи
        print("\n🔍 6/6: ДОДАТКОВІ АНАЛІЗИ")
        print("-" * 40)

        # Спробуємо імпортувати та запустити додаткові аналізи
        try:
            from analysis.bonus_analysis import analyze_bonus_system

            print("🎁 Аналіз бонусної системи...")
            await analyze_bonus_system()
        except ImportError:
            print("⚠️ Модуль bonus_analysis не знайдено")
        except Exception as e:
            print(f"⚠️ Помилка в аналізі бонусів: {e}")

        try:
            from analysis.deep_duplicate_analysis import run_deep_duplicate_analysis

            print("🔍 Глибокий аналіз дублікатів...")
            await run_deep_duplicate_analysis()
        except ImportError:
            print("⚠️ Модуль deep_duplicate_analysis не знайдено")
        except Exception as e:
            print(f"⚠️ Помилка в аналізі дублікатів: {e}")

        print("\n" + "=" * 80)
        print("✅ УСІ АНАЛІЗИ ЗАВЕРШЕНО УСПІШНО!")
        print(f"⏰ Завершено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Помилка при виконанні аналізу: {e}")
        import traceback

        traceback.print_exc()


def main():
    """Головна функція"""

    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "html":
            # Новий режим з HTML звітом
            asyncio.run(run_all_analysis_with_html())
        elif mode == "legacy":
            # Старий режим
            asyncio.run(run_legacy_analysis())
        elif mode == "help" or mode == "--help" or mode == "-h":
            # Довідка
            print("🚀 СИСТЕМА АНАЛІЗУ ПРОДАЖІВ AVOCADO")
            print("=" * 50)
            print("\n📋 Доступні режими запуску:")
            print("\n🎨 HTML звітність:")
            print("  python run_analysis_html.py html")
            print("  python run_analysis_html.py        (за замовчуванням)")
            print("  - Генерує професійний HTML звіт")
            print("  - Автоматично відкриває в браузері")
            print("  - Включає всі типи аналізів")

            print("\n📊 Legacy режим (консольний):")
            print("  python run_analysis_html.py legacy")
            print("  - Виводить результати в консоль")
            print("  - Запускає оригінальні аналітичні модулі")
            print("  - Включає додаткові експериментальні аналізи")

            print("\n❓ Довідка:")
            print("  python run_analysis_html.py help")
            print("  python run_analysis_html.py --help")
            print("  python run_analysis_html.py -h")

            print("\n🔧 Приклади використання:")
            print("  # Швидкий HTML звіт")
            print("  python run_analysis_html.py")
            print("\n  # Детальний консольний аналіз")
            print("  python run_analysis_html.py legacy")

            print("\n📁 Файли звітів зберігаються в:")
            print("  analysis/reports/")
            print("=" * 50)
        else:
            print("❌ Невідомий режим!")
            print("✅ Доступні режими:")
            print("  - python run_analysis_html.py html     (HTML звіт)")
            print("  - python run_analysis_html.py legacy   (оригінальні аналізи)")
            print("  - python run_analysis_html.py help     (довідка)")
            print(
                "  - python run_analysis_html.py          (HTML звіт за замовчуванням)"
            )
    else:
        # За замовчуванням - HTML режим
        asyncio.run(run_all_analysis_with_html())


if __name__ == "__main__":
    main()
