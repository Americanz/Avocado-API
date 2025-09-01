#!/usr/bin/env python3
"""
Тестування PostgreSQL функцій LUCHAN
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()


async def test_luchan_functions():
    """Тестування функцій"""
    conn = await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "avocado_db"),
        user=os.getenv("POSTGRES_USER", "avocado_user"),
        password=os.getenv("POSTGRES_PASSWORD", "avocado_pass"),
    )

    print("🧪 ТЕСТУВАННЯ POSTGRESQL ФУНКЦІЙ LUCHAN")
    print("=" * 60)

    # 1. Список всіх створених функцій
    print("\n📋 СТВОРЕНІ ФУНКЦІЇ:")
    query = """
    SELECT
        routine_name,
        routine_type,
        data_type
    FROM information_schema.routines
    WHERE routine_schema = 'public'
    AND routine_name ~ '^(get_|find_|calculate_)'
    ORDER BY routine_name;
    """

    functions = await conn.fetch(query)
    for func in functions:
        print(
            f"   🔧 {func['routine_name']} ({func['routine_type']}) -> {func['data_type']}"
        )

    # 2. Тест get_spot_revenue (працює)
    print("\n✅ ТЕСТ: Дохід точки за серпень")
    try:
        result = await conn.fetchrow(
            "SELECT * FROM get_spot_revenue($1, $2::DATE, $3::DATE)",
            1,
            "2025-08-01",
            "2025-08-31",
        )
        if result:
            spot_name, transactions, revenue, avg_check, max_check = result
            print(f"   📊 {spot_name}: {transactions:,} транзакцій")
            print(f"   💰 Дохід: {revenue:,.2f} грн")
            print(f"   📈 Середній чек: {avg_check:.2f} грн")
            print(f"   🔝 Макс чек: {max_check:.2f} грн")
    except Exception as e:
        print(f"   ❌ Помилка: {e}")

    # 3. Тест get_top_products
    print("\n📦 ТЕСТ: ТОП продукти")
    try:
        # Спробуємо різні варіанти виклику
        result = await conn.fetch("SELECT * FROM get_top_products(5)")
        print(f"   ✅ Знайдено {len(result)} продуктів")
        for i, row in enumerate(result[:3], 1):
            print(f"   {i}. {dict(row)}")
    except Exception as e:
        print(f"   ❌ get_top_products(5): {e}")

        # Спробуємо без параметрів
        try:
            result = await conn.fetch("SELECT * FROM get_top_products()")
            print(f"   ✅ get_top_products(): {len(result)} результатів")
        except Exception as e2:
            print(f"   ❌ get_top_products(): {e2}")

    # 4. Тест сезонної аналітики
    print("\n📅 ТЕСТ: Сезонна аналітика")
    try:
        result = await conn.fetch("SELECT * FROM get_seasonal_analytics()")
        print(f"   ✅ Сезонна аналітика: {len(result)} результатів")
        for i, row in enumerate(result[:2], 1):
            print(f"   {i}. {dict(row)}")
    except Exception as e:
        print(f"   ❌ Помилка: {e}")

    # 5. Тест погодинної продуктивності
    print("\n⏰ ТЕСТ: Погодинна продуктивність точки")
    try:
        result = await conn.fetch("SELECT * FROM get_spot_hourly_performance(1)")
        print(f"   ✅ Погодинна статистика: {len(result)} результатів")
        for i, row in enumerate(result[:3], 1):
            print(f"   {i}. {dict(row)}")
    except Exception as e:
        print(f"   ❌ Помилка: {e}")

    print("\n" + "=" * 60)
    print("✅ ТЕСТУВАННЯ ЗАВЕРШЕНО")
    print("=" * 60)

    await conn.close()


if __name__ == "__main__":
    asyncio.run(test_luchan_functions())
