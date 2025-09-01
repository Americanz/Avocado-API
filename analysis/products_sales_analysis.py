#!/usr/bin/env python3
"""
Аналіз продажів по товарах
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


async def analyze_products_sales():
    """Аналіз продажів по товарах"""
    from src.core.database.connection import AsyncSessionLocal
    from src.features.telegram_bot.models.product import Product
    from src.features.telegram_bot.models.transaction_product import (
        TransactionProduct,
    )
    from src.features.telegram_bot.models.transaction import Transaction
    from sqlalchemy import select, func, desc, and_

    async with AsyncSessionLocal() as session:
        print("🛍️ АНАЛІЗ ПРОДАЖІВ ПО ТОВАРАХ")
        print("=" * 60)

        # 1. ТОП-20 найпродаваніших товарів за кількістю
        print("📊 ТОП-20 НАЙПРОДАВАНІШИХ ТОВАРІВ ЗА КІЛЬКІСТЮ:")
        print("-" * 60)

        top_by_quantity_query = (
            select(
                Product.product_name,
                Product.category_name,
                func.sum(TransactionProduct.count).label("total_quantity"),
                func.count(TransactionProduct.id).label("order_count"),
                func.sum(TransactionProduct.sum).label("total_revenue"),
                func.avg(TransactionProduct.sum / TransactionProduct.count).label(
                    "avg_price"
                ),
            )
            .select_from(Product)
            .join(
                TransactionProduct,
                Product.poster_product_id == TransactionProduct.poster_product_id,
            )
            .group_by(Product.product_name, Product.category_name)
            .order_by(desc("total_quantity"))
            .limit(20)
        )

        quantity_result = await session.execute(top_by_quantity_query)
        top_quantity = quantity_result.all()

        for i, product in enumerate(top_quantity, 1):
            avg_price = float(product.avg_price or 0)
            total_rev = float(product.total_revenue or 0)

            print(f"{i:2d}. {product.product_name}")
            print(f"    📂 Категорія: {product.category_name}")
            print(f"    📦 Продано: {product.total_quantity} шт")
            print(f"    🔢 Замовлень: {product.order_count}")
            print(f"    💰 Оборот: {total_rev:,.2f} грн")
            print(f"    💵 Середня ціна: {avg_price:.2f} грн")
            print()

        # 2. ТОП-15 найприбутковіших товарів
        print("=" * 60)
        print("💰 ТОП-15 НАЙПРИБУТКОВІШИХ ТОВАРІВ:")
        print("-" * 60)

        top_by_revenue_query = (
            select(
                Product.product_name,
                Product.category_name,
                func.sum(TransactionProduct.sum).label("total_revenue"),
                func.sum(TransactionProduct.count).label("total_quantity"),
                func.count(TransactionProduct.id).label("order_count"),
                func.avg(TransactionProduct.sum / TransactionProduct.count).label(
                    "avg_price"
                ),
            )
            .select_from(Product)
            .join(
                TransactionProduct,
                Product.poster_product_id == TransactionProduct.poster_product_id,
            )
            .group_by(Product.product_name, Product.category_name)
            .order_by(desc("total_revenue"))
            .limit(15)
        )

        revenue_result = await session.execute(top_by_revenue_query)
        top_revenue = revenue_result.all()

        for i, product in enumerate(top_revenue, 1):
            total_rev = float(product.total_revenue)
            avg_price = float(product.avg_price or 0)

            print(f"{i:2d}. {product.product_name}")
            print(f"    📂 {product.category_name}")
            print(f"    💰 Оборот: {total_rev:,.2f} грн")
            print(f"    📦 Продано: {product.total_quantity} шт")
            print(f"    💵 Середня ціна: {avg_price:.2f} грн")
            print()

        # 3. Аналіз по категоріях
        print("=" * 60)
        print("📂 АНАЛІЗ ПО КАТЕГОРІЯХ:")
        print("-" * 60)

        category_query = (
            select(
                Product.category_name,
                func.count(func.distinct(Product.poster_product_id)).label(
                    "unique_products"
                ),
                func.sum(TransactionProduct.count).label("total_quantity"),
                func.sum(TransactionProduct.sum).label("total_revenue"),
                func.avg(TransactionProduct.sum / TransactionProduct.count).label(
                    "avg_price"
                ),
            )
            .select_from(Product)
            .join(
                TransactionProduct,
                Product.poster_product_id == TransactionProduct.poster_product_id,
            )
            .group_by(Product.category_name)
            .order_by(desc("total_revenue"))
        )

        category_result = await session.execute(category_query)
        categories = category_result.all()

        for i, category in enumerate(categories, 1):
            total_rev = float(category.total_revenue)
            avg_price = float(category.avg_price or 0)

            print(f"{i:2d}. {category.category_name}")
            print(f"    🏷️  Унікальних товарів: {category.unique_products}")
            print(f"    📦 Всього продано: {category.total_quantity} шт")
            print(f"    💰 Оборот: {total_rev:,.2f} грн")
            print(f"    💵 Середня ціна: {avg_price:.2f} грн")
            print()

        # 4. Товари з найвищою середньою ціною (топ-10)
        print("=" * 60)
        print("💎 ТОП-10 НАЙДОРОЖЧИХ ТОВАРІВ (за середньою ціною):")
        print("-" * 60)

        expensive_query = (
            select(
                Product.product_name,
                Product.category_name,
                func.avg(TransactionProduct.sum / TransactionProduct.count).label(
                    "avg_price"
                ),
                func.sum(TransactionProduct.count).label("total_quantity"),
                func.sum(TransactionProduct.sum).label("total_revenue"),
            )
            .select_from(Product)
            .join(
                TransactionProduct,
                Product.poster_product_id == TransactionProduct.poster_product_id,
            )
            .group_by(Product.product_name, Product.category_name)
            .having(func.sum(TransactionProduct.count) >= 10)  # Мінімум 10 продажів
            .order_by(desc("avg_price"))
            .limit(10)
        )

        expensive_result = await session.execute(expensive_query)
        expensive_products = expensive_result.all()

        for i, product in enumerate(expensive_products, 1):
            avg_price = float(product.avg_price)
            total_rev = float(product.total_revenue)

            print(f"{i:2d}. {product.product_name}")
            print(f"    📂 {product.category_name}")
            print(f"    💵 Середня ціна: {avg_price:.2f} грн")
            print(f"    📦 Продано: {product.total_quantity} шт")
            print(f"    💰 Оборот: {total_rev:,.2f} грн")
            print()

        # 5. Загальна статистика
        print("=" * 60)
        print("🎯 ЗАГАЛЬНА СТАТИСТИКА ПО ТОВАРАХ:")
        print("-" * 60)

        # Загальна статистика
        total_stats_query = (
            select(
                func.count(func.distinct(Product.poster_product_id)).label(
                    "unique_products"
                ),
                func.sum(TransactionProduct.count).label("total_quantity"),
                func.sum(TransactionProduct.sum).label("total_revenue"),
                func.avg(TransactionProduct.sum / TransactionProduct.count).label(
                    "avg_price"
                ),
                func.count(TransactionProduct.id).label("total_orders"),
            )
            .select_from(Product)
            .join(
                TransactionProduct,
                Product.poster_product_id == TransactionProduct.poster_product_id,
            )
        )

        stats_result = await session.execute(total_stats_query)
        stats = stats_result.first()

        if stats:
            print(f"🏷️  Унікальних товарів: {stats.unique_products}")
            print(f"📦 Всього продано: {stats.total_quantity:,} шт")
            print(f"🔢 Всього замовлень: {stats.total_orders:,}")
            print(f"💰 Загальний оборот: {float(stats.total_revenue):,.2f} грн")
            print(f"💵 Середня ціна за одиницю: {float(stats.avg_price):.2f} грн")


if __name__ == "__main__":
    asyncio.run(analyze_products_sales())
