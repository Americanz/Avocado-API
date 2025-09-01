#!/usr/bin/env python3
"""
Скрипт для перевірки бонусної інформації клієнта
Показує поточний баланс, історію операцій та транзакції
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from src.config.settings import settings


def format_datetime(dt):
    """Форматування дати та часу"""
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return "N/A"


def format_amount(amount):
    """Форматування суми"""
    if amount is not None:
        return f"{amount:.2f}"
    return "0.00"


def format_client_balance(balance_kopecks):
    """Форматування балансу клієнта (конвертація з копійок в гривні)"""
    if balance_kopecks is not None:
        return f"{(balance_kopecks / 100):.2f}"
    return "0.00"


def get_client_bonus_info(client_id):
    """Отримати повну інформацію по бонусах клієнта"""

    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        # 1. Базова інформація про клієнта
        client_info = conn.execute(
            text(
                """
            SELECT
                client_id,
                COALESCE(firstname || ' ' || lastname, phone) as name,
                phone,
                bonus,
                created_at,
                updated_at
            FROM clients
            WHERE client_id = :client_id
        """
            ),
            {"client_id": client_id},
        ).fetchone()

        if not client_info:
            print(f"❌ Клієнт з ID {client_id} не знайдений!")
            return

        print("=" * 80)
        print(f"🧑‍💼 ІНФОРМАЦІЯ ПРО КЛІЄНТА #{client_id}")
        print("=" * 80)
        print(f"📛 Ім'я: {client_info[1] or 'Не вказано'}")
        print(f"📞 Телефон: {client_info[2] or 'Не вказано'}")
        print(f"💰 Поточний баланс бонусів: {format_client_balance(client_info[3])}")
        print(f"📅 Створено: {format_datetime(client_info[4])}")
        print(f"🔄 Оновлено: {format_datetime(client_info[5])}")

        # 2. Статистика бонусних операцій
        bonus_stats = conn.execute(
            text(
                """
            SELECT
                operation_type,
                COUNT(*) as count,
                SUM(amount) as total_amount,
                MAX(processed_at) as last_operation
            FROM transaction_bonus
            WHERE client_id = :client_id
            GROUP BY operation_type
            ORDER BY operation_type
        """
            ),
            {"client_id": client_id},
        ).fetchall()

        print(f"\n📊 СТАТИСТИКА БОНУСНИХ ОПЕРАЦІЙ")
        print("-" * 80)
        if bonus_stats:
            total_earned = 0
            total_spent = 0

            for stat in bonus_stats:
                op_type = stat[0]
                count = stat[1]
                amount = stat[2] or 0
                amount_grn = float(amount) / 100.0  # Конвертуємо з копійок в гривні
                last_op = format_datetime(stat[3])

                if op_type == "EARN":
                    total_earned += amount_grn
                    print(
                        f"💚 Нараховано: {count} операцій, +{format_amount(amount_grn)} (останнє: {last_op})"
                    )
                elif op_type == "SPEND":
                    total_spent += abs(amount_grn)  # amount негативний для SPEND
                    print(
                        f"💸 Витрачено: {count} операцій, {format_amount(amount_grn)} (останнє: {last_op})"
                    )
                else:
                    print(
                        f"🔄 {op_type}: {count} операцій, {format_amount(amount_grn)} (останнє: {last_op})"
                    )

            print(f"\n📈 Всього нараховано: +{format_amount(total_earned)}")
            print(f"📉 Всього витрачено: -{format_amount(total_spent)}")
            print(
                f"🧮 Розрахунковий баланс: {format_amount(total_earned - total_spent)}"
            )
        else:
            print("❌ Немає бонусних операцій")

        # 3. Історія бонусних операцій (останні 10)
        bonus_history = conn.execute(
            text(
                """
            SELECT
                id,
                transaction_id,
                operation_type,
                amount,
                balance_before,
                balance_after,
                description,
                processed_at
            FROM transaction_bonus
            WHERE client_id = :client_id
            ORDER BY processed_at DESC
            LIMIT 10
        """
            ),
            {"client_id": client_id},
        ).fetchall()

        print(f"\n📋 ОСТАННІ БОНУСНІ ОПЕРАЦІЇ (топ 10)")
        print("-" * 80)
        if bonus_history:
            for op in bonus_history:
                op_id = op[0]
                tx_id = op[1] or "N/A"
                op_type = op[2]
                amount = format_client_balance(
                    op[3]
                )  # Конвертуємо amount з копійок в гривні
                balance_before = format_client_balance(
                    op[4]
                )  # Конвертуємо з копійок в гривні
                balance_after = format_client_balance(
                    op[5]
                )  # Конвертуємо з копійок в гривні
                description = op[6] or "Без опису"
                processed_at = format_datetime(op[7])

                # Символи для типів операцій
                symbol = {
                    "EARN": "💚 +",
                    "SPEND": "💸 ",
                    "ADJUST": "🔄 ",
                    "EXPIRE": "⏰ ",
                }.get(op_type, "❓ ")

                print(f"{symbol}{amount} | {balance_before} → {balance_after}")
                print(f"   📅 {processed_at} | TX: {tx_id}")
                print(f"   📝 {description}")
                print()
        else:
            print("❌ Немає операцій")

        # 4. Транзакції клієнта з бонусами (останні 10) + інформація про Spot та товари
        transactions = conn.execute(
            text(
                """
            SELECT
                t.transaction_id,
                t.sum,
                t.bonus,
                t.payed_bonus,
                t.date_close,
                COUNT(tb.id) as bonus_operations,
                s.name as spot_name,
                s.address as spot_address,
                STRING_AGG(
                    DISTINCT p.product_name || ' (' || tp.count || ' шт. × ' || tp.price || ' грн)',
                    '|SPLIT|'
                    ORDER BY p.product_name || ' (' || tp.count || ' шт. × ' || tp.price || ' грн)'
                ) as products_list
            FROM transactions t
            LEFT JOIN transaction_bonus tb ON t.transaction_id = tb.transaction_id
            LEFT JOIN spots s ON t.spot = s.spot_id
            LEFT JOIN transaction_products tp ON t.transaction_id = tp.transaction_id
            LEFT JOIN products p ON tp.product = p.poster_product_id
            WHERE t.client_id = :client_id
            AND t.date_close IS NOT NULL
            GROUP BY t.transaction_id, t.sum, t.bonus, t.payed_bonus, t.date_close, s.name, s.address
            ORDER BY t.date_close DESC
            LIMIT 10
        """
            ),
            {"client_id": client_id},
        ).fetchall()

        print(f"🛒 ОСТАННІ ТРАНЗАКЦІЇ З БОНУСАМИ (топ 10)")
        print("-" * 80)
        if transactions:
            for tx in transactions:
                tx_id = tx[0]
                tx_sum = format_amount(tx[1])
                bonus_percent = format_amount(tx[2]) if tx[2] else "0.00"
                paid_bonus = format_amount(tx[3]) if tx[3] else "0.00"
                date_close = format_datetime(tx[4])
                bonus_ops = tx[5]
                spot_name = tx[6] or "Невідомий заклад"
                spot_address = tx[7] or "Адреса не вказана"
                products_list = tx[8] or "Товари не знайдені"

                # Розрахунок нарахованих бонусів
                if tx[1] and tx[2]:
                    earned_bonus = format_amount(tx[1] * tx[2] / 100)
                else:
                    earned_bonus = "0.00"

                print(f"🧾 Транзакція #{tx_id}")
                print(f"   🏪 Заклад: {spot_name}")
                print(f"   📍 Адреса: {spot_address}")
                print(
                    f"   💰 Сума: {tx_sum} | Бонус %: {bonus_percent}% | Нараховано: +{earned_bonus}"
                )
                print(f"   💸 Оплачено бонусами: -{paid_bonus}")
                print(f"   📅 Дата: {date_close}")
                print(f"   🔄 Бонусних операцій: {bonus_ops}")

                # Красиве відображення товарів
                if products_list and products_list != "Товари не знайдені":
                    print(f"   🛍️ Товари:")
                    products = products_list.split("|SPLIT|")
                    for i, product in enumerate(products, 1):
                        print(f"      {i}. {product}")
                else:
                    print(f"   🛍️ Товари: не знайдені")
                print()
        else:
            print("❌ Немає транзакцій")

        # 5. Перевірка цілісності даних
        print(f"🔍 ПЕРЕВІРКА ЦІЛІСНОСТІ ДАНИХ")
        print("-" * 80)

        # Перевірка балансу
        calculated_balance = conn.execute(
            text(
                """
            SELECT COALESCE(SUM(amount), 0) as calculated_balance
            FROM transaction_bonus
            WHERE client_id = :client_id
        """
            ),
            {"client_id": client_id},
        ).scalar()

        current_balance = client_info[3] or 0

        print(f"💰 Поточний баланс в clients: {format_client_balance(current_balance)}")
        print(f"🧮 Розрахований баланс з операцій: {format_client_balance(calculated_balance)}")

        # Конвертуємо обидва баланси в гривні для порівняння
        current_balance_grn = current_balance / 100
        calculated_balance_grn = calculated_balance / 100
        if abs(current_balance_grn - calculated_balance_grn) < 0.01:  # допуск на округлення
            print("✅ Баланс збігається!")
        else:
            print("❌ ПОМИЛКА: Баланси не збігаються!")

        # Перевірка останньої операції
        last_bonus_update = conn.execute(
            text(
                """
            SELECT MAX(processed_at) as last_bonus_op
            FROM transaction_bonus
            WHERE client_id = :client_id
        """
            ),
            {"client_id": client_id},
        ).scalar()

        if last_bonus_update:
            print(f"⏰ Остання бонусна операція: {format_datetime(last_bonus_update)}")
            print(f"🔄 Оновлення клієнта: {format_datetime(client_info[5])}")

        print("=" * 80)


def main():
    """Головна функція"""
    if len(sys.argv) < 2:
        print("🔍 Скрипт для перевірки бонусної інформації клієнта")
        print("\nВикористання:")
        print("  python check_client_bonus.py <client_id>")
        print("\nПриклади:")
        print("  python check_client_bonus.py 2415")
        print("  python check_client_bonus.py 9652")

        # Запропонувати клієнтів з бонусними операціями
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            sample_clients = conn.execute(
                text(
                    """
                SELECT DISTINCT tb.client_id,
                       COALESCE(c.firstname || ' ' || c.lastname, c.phone) as name,
                       c.phone, c.bonus
                FROM transaction_bonus tb
                INNER JOIN clients c ON tb.client_id = c.client_id
                ORDER BY c.bonus DESC
                LIMIT 5
            """
                )
            ).fetchall()

            if sample_clients:
                print("\n🎯 Клієнти з бонусними операціями:")
                for client in sample_clients:
                    name = client[1] or "Без імені"
                    phone = client[2] or "Без телефону"
                    balance = format_client_balance(client[3])
                    print(f"  ID: {client[0]} | {name} | {phone} | Баланс: {balance}")

        return

    try:
        client_id = int(sys.argv[1])
        get_client_bonus_info(client_id)
    except ValueError:
        print("❌ Помилка: Client ID повинен бути числом!")
    except Exception as e:
        print(f"❌ Помилка: {e}")


if __name__ == "__main__":
    main()
