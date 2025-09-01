#!/usr/bin/env python3
"""
Розгортання PostgreSQL функцій для LUCHAN
"""

import asyncio
import asyncpg
from pathlib import Path
import os
import sys
from dotenv import load_dotenv

# Завантажуємо змінні середовища
load_dotenv()


class FunctionDeployer:
    def __init__(self):
        # Отримуємо параметри підключення з .env
        self.db_host = os.getenv("POSTGRES_HOST", "localhost")
        self.db_port = int(os.getenv("POSTGRES_PORT", "5432"))
        self.db_name = os.getenv("POSTGRES_DB", "avocado_db")
        self.db_user = os.getenv("POSTGRES_USER", "avocado_user")
        self.db_password = os.getenv("POSTGRES_PASSWORD", "avocado_pass")

        self.functions_dir = Path(__file__).parent

        print(f"🔗 Підключення до: {self.db_host}:{self.db_port}/{self.db_name}")

    async def connect_db(self):
        """Підключення до бази даних"""
        try:
            self.conn = await asyncpg.connect(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
            )
            print("✅ Підключено до бази даних")
            return True
        except Exception as e:
            print(f"❌ Помилка підключення до БД: {e}")
            return False

    async def close_db(self):
        """Закриття підключення"""
        if hasattr(self, "conn") and self.conn:
            await self.conn.close()
            print("📝 Підключення закрито")

    async def deploy_functions_from_file(self, filename):
        """Розгортання функцій з файлу"""
        file_path = self.functions_dir / filename

        if not file_path.exists():
            print(f"❌ Файл {filename} не знайдено")
            return False

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                sql_content = f.read()

            # Виконуємо весь файл як один блок (PostgreSQL підтримує це)
            print(f"📄 Розгортання функцій з {filename}...")

            try:
                await self.conn.execute(sql_content)
                print(f"   ✅ Всі функції з {filename} виконано успішно")
            except Exception as e:
                print(f"   ⚠️  Помилка виконання: {e}")
                print(f"   🔄 Спробуємо розділити на окремі функції...")

                # Якщо є помилка, спробуємо розділити по функціях
                functions = []
                current_function = []

                for line in sql_content.split("\n"):
                    if (
                        line.strip().startswith("CREATE OR REPLACE FUNCTION")
                        and current_function
                    ):
                        # Зберігаємо попередню функцію
                        functions.append("\n".join(current_function))
                        current_function = [line]
                    else:
                        current_function.append(line)

                # Додаємо останню функцію
                if current_function:
                    functions.append("\n".join(current_function))

                # Виконуємо кожну функцію окремо
                for i, func in enumerate(functions, 1):
                    if func.strip():
                        try:
                            await self.conn.execute(func)
                            print(f"   ✅ Функція {i}/{len(functions)} виконана")
                        except Exception as func_error:
                            print(f"   ❌ Помилка в функції {i}: {func_error}")

            print(f"✅ Обробка {filename} завершена")
            return True

        except Exception as e:
            print(f"❌ Помилка при розгортанні {filename}: {e}")
            return False

    async def test_functions(self):
        """Тестування розгорнутих функцій"""
        print("\n🧪 ТЕСТУВАННЯ ФУНКЦІЙ:")
        print("=" * 50)

        test_queries = [
            {
                "name": "get_spot_revenue",
                "query": "SELECT get_spot_revenue(1, '2025-08-01', '2025-08-31')",
                "description": "Оборот точки за серпень",
            },
            {
                "name": "get_top_products",
                "query": "SELECT * FROM get_top_products(5)",
                "description": "ТОП-5 продуктів",
            },
            {
                "name": "get_client_stats",
                "query": "SELECT * FROM get_client_stats() LIMIT 3",
                "description": "Статистика клієнтів",
            },
            {
                "name": "calculate_revenue_growth",
                "query": "SELECT calculate_revenue_growth('2025-07-01', '2025-08-31')",
                "description": "Ріст обороту",
            },
        ]

        for test in test_queries:
            try:
                print(f"\n🔍 Тест: {test['description']}")
                result = await self.conn.fetch(test["query"])
                print(f"   ✅ {test['name']}: OK ({len(result)} результатів)")

                # Показуємо перший результат для прикладу
                if result:
                    print(f"   📊 Приклад: {dict(result[0])}")

            except Exception as e:
                print(f"   ❌ {test['name']}: {e}")

    async def list_deployed_functions(self):
        """Список розгорнутих функцій"""
        print("\n📋 РОЗГОРНУТІ ФУНКЦІЇ:")
        print("=" * 50)

        query = """
        SELECT
            routine_name as function_name,
            routine_type as type,
            data_type as return_type
        FROM information_schema.routines
        WHERE routine_schema = 'public'
        AND (routine_name LIKE '%luchan%'
             OR routine_name LIKE 'get_%'
             OR routine_name LIKE 'calculate_%'
             OR routine_name LIKE '%spot%'
             OR routine_name LIKE '%client%'
             OR routine_name LIKE '%product%')
        ORDER BY routine_name;
        """

        try:
            functions = await self.conn.fetch(query)

            if functions:
                for func in functions:
                    print(
                        f"   🔧 {func['function_name']} ({func['type']}) -> {func['return_type']}"
                    )
            else:
                print("   ⚠️  Функції не знайдено")

        except Exception as e:
            print(f"   ❌ Помилка отримання списку функцій: {e}")

    async def deploy_all(self):
        """Розгортання всіх функцій"""
        print("🚀 РОЗГОРТАННЯ POSTGRESQL ФУНКЦІЙ ДЛЯ LUCHAN")
        print("=" * 60)

        if not await self.connect_db():
            return False

        try:
            # Розгортаємо бізнес-аналітичні функції
            await self.deploy_functions_from_file("business_analytics_functions.sql")

            # Розгортаємо операційні функції
            await self.deploy_functions_from_file("operational_functions.sql")

            # Показуємо список функцій
            await self.list_deployed_functions()

            # Тестуємо функції
            await self.test_functions()

            print("\n" + "=" * 60)
            print("✅ РОЗГОРТАННЯ ЗАВЕРШЕНО УСПІШНО!")
            print("=" * 60)

            return True

        except Exception as e:
            print(f"❌ Загальна помилка розгортання: {e}")
            return False

        finally:
            await self.close_db()


async def main():
    """Головна функція"""
    deployer = FunctionDeployer()
    success = await deployer.deploy_all()

    if success:
        print("\n💡 Тепер ви можете використовувати функції в SQL запитах:")
        print("   SELECT get_spot_revenue(1, '2025-08-01', '2025-08-31');")
        print("   SELECT * FROM get_top_products(10);")
        print("   SELECT * FROM get_client_stats();")
    else:
        print("\n❌ Розгортання не вдалося. Перевірте підключення до БД.")


if __name__ == "__main__":
    asyncio.run(main())
