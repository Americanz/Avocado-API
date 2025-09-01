##!/usr/bin/env python3
"""
Скрипт для тестування бонусної системи після розгортання
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime

def test_bonus_system():
    """Тестування всіх компонентів бонусної системи"""

    # Підключення до бази даних
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="avocado_db",
            user="avocado_user",
            password="avocado_pass"
        )        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="avocado_db",
            user="avocado_user",
            password="avocado_pass"
        )
"""
Скрипт для тестування бонусної системи після розгортання
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime


def test_bonus_system():
    """Тестування всіх компонентів бонусної системи"""

    # Підключення до бази даних
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=15432,
            database="avocado_db",
            user="avocado_user",
            password="avocado_pass",
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        print("✅ Підключення до бази даних успішне")
    except Exception as e:
        print(f"❌ Помилка підключення до бази: {e}")
        return False

    tests_passed = 0
    total_tests = 0

    # Тест 1: Перевірка таблиць
    total_tests += 1
    try:
        cursor.execute(
            """
            SELECT table_name FROM information_schema.tables
            WHERE table_name IN ('system_settings', 'transaction_bonus')
        """
        )
        tables = [row["table_name"] for row in cursor.fetchall()]

        if "system_settings" in tables and "transaction_bonus" in tables:
            print("✅ Тест 1: Таблиці створені успішно")
            tests_passed += 1
        else:
            print(f"❌ Тест 1: Відсутні таблиці. Знайдено: {tables}")
    except Exception as e:
        print(f"❌ Тест 1: Помилка перевірки таблиць: {e}")

    # Тест 2: Перевірка налаштувань
    total_tests += 1
    try:
        cursor.execute("SELECT key, value FROM system_settings WHERE key LIKE 'bonus%'")
        settings = {row["key"]: row["value"] for row in cursor.fetchall()}

        required_settings = ["bonus_system_enabled", "bonus_system_start_date"]
        missing = [s for s in required_settings if s not in settings]

        if not missing:
            print("✅ Тест 2: Налаштування бонусної системи присутні")
            tests_passed += 1
            for key, value in settings.items():
                print(f"   📋 {key}: {value}")
        else:
            print(f"❌ Тест 2: Відсутні налаштування: {missing}")
    except Exception as e:
        print(f"❌ Тест 2: Помилка перевірки налаштувань: {e}")

    # Тест 3: Перевірка тригерів
    total_tests += 1
    try:
        cursor.execute(
            """
            SELECT trigger_name, event_object_table, action_timing, event_manipulation
            FROM information_schema.triggers
            WHERE trigger_name = 'trigger_process_bonus_operations'
        """
        )
        triggers = cursor.fetchall()

        if triggers:
            print("✅ Тест 3: Тригер бонусних операцій активний")
            tests_passed += 1
            for trigger in triggers:
                print(
                    f"   ⚡ {trigger['trigger_name']} на {trigger['event_object_table']} ({trigger['action_timing']} {trigger['event_manipulation']})"
                )
        else:
            print("❌ Тест 3: Тригер бонусних операцій не знайдено")
    except Exception as e:
        print(f"❌ Тест 3: Помилка перевірки тригерів: {e}")

    # Тест 4: Перевірка функцій
    total_tests += 1
    try:
        cursor.execute(
            """
            SELECT routine_name FROM information_schema.routines
            WHERE routine_name IN ('process_bonus_operations', 'manage_bonus_triggers', 'process_bonus_operations_manual')
            AND routine_type = 'FUNCTION'
        """
        )
        functions = [row["routine_name"] for row in cursor.fetchall()]

        required_functions = [
            "process_bonus_operations",
            "manage_bonus_triggers",
            "process_bonus_operations_manual",
        ]
        missing_functions = [f for f in required_functions if f not in functions]

        if not missing_functions:
            print("✅ Тест 4: Всі необхідні функції створені")
            tests_passed += 1
            for func in functions:
                print(f"   🔧 {func}()")
        else:
            print(f"❌ Тест 4: Відсутні функції: {missing_functions}")
    except Exception as e:
        print(f"❌ Тест 4: Помилка перевірки функцій: {e}")

    # Тест 5: Перевірка існуючих бонусних операцій
    total_tests += 1
    try:
        cursor.execute(
            """
            SELECT
                COUNT(*) as total_operations,
                COUNT(DISTINCT client_id) as unique_clients,
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) / 100.0 as total_earned,
                SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) / 100.0 as total_spent
            FROM transaction_bonus
        """
        )
        stats = cursor.fetchone()

        if stats["total_operations"] > 0:
            print("✅ Тест 5: Є бонусні операції в системі")
            tests_passed += 1
            print(f"   📊 Операцій: {stats['total_operations']}")
            print(f"   👥 Клієнтів: {stats['unique_clients']}")
            print(f"   💚 Нараховано: {stats['total_earned']:.2f} грн")
            print(f"   💸 Витрачено: {stats['total_spent']:.2f} грн")
        else:
            print(
                "⚠️  Тест 5: Бонусні операції відсутні (це нормально для нової системи)"
            )
            tests_passed += 1  # Це не помилка для нової системи
    except Exception as e:
        print(f"❌ Тест 5: Помилка перевірки операцій: {e}")

    # Тест 6: Тест функції управління тригерами
    total_tests += 1
    try:
        cursor.execute("SELECT manage_bonus_triggers(true)")
        result = cursor.fetchone()

        if result and "ENABLED" in str(result[0]):
            print("✅ Тест 6: Функція управління тригерами працює")
            tests_passed += 1
        else:
            print(f"❌ Тест 6: Неочікуваний результат функції: {result}")
    except Exception as e:
        print(f"❌ Тест 6: Помилка тестування функції управління: {e}")

    # Фінальний звіт
    print("\n" + "=" * 60)
    print(f"📊 РЕЗУЛЬТАТИ ТЕСТУВАННЯ БОНУСНОЇ СИСТЕМИ")
    print("=" * 60)
    print(f"✅ Пройдено: {tests_passed}/{total_tests} тестів")

    if tests_passed == total_tests:
        print("🎉 Всі тести пройдені! Бонусна система готова до роботи.")
    elif tests_passed >= total_tests * 0.8:
        print("⚠️  Більшість тестів пройдена, але є деякі проблеми.")
    else:
        print("❌ Критичні помилки! Потрібне додаткове налаштування.")

    print("=" * 60)

    cursor.close()
    conn.close()

    return tests_passed == total_tests


if __name__ == "__main__":
    print("🔍 ТЕСТУВАННЯ БОНУСНОЇ СИСТЕМИ")
    print("=" * 60)
    print(f"📅 Час тестування: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    success = test_bonus_system()

    if success:
        print("\n🚀 Система готова! Можете використовувати:")
        print("   • python script/check_client_bonus.py <client_id>")
        print("   • python script/sync/sync_poster_receipts.py today")
    else:
        print("\n🔧 Потрібно додаткове налаштування системи")
