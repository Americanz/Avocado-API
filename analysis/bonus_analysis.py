"""
Bonus field analysis in clients and its relation to transactions
"""

import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "ASYNC_DATABASE_URL",
    "postgresql+asyncpg://avocado_user:avocado_pass@localhost:5432/avocado_db",
)


async def bonus_analysis():
    """Analyze bonus field and its relation to transactions"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as session:
        try:
            print("💰 BONUS FIELD ANALYSIS")
            print("=" * 50)

            # Basic bonus statistics
            print("\n📊 Basic bonus statistics:")

            total_clients = await session.scalar(
                text(
                    """
                SELECT COUNT(*) FROM clients                WHERE phone IS NOT NULL AND phone != ''
            """
                )
            )

            clients_with_bonus = await session.scalar(
                text(
                    """
                SELECT COUNT(*) FROM clients                WHERE phone IS NOT NULL AND phone != ''
                AND bonus IS NOT NULL AND bonus > 0
            """
                )
            )

            avg_bonus = await session.scalar(
                text(
                    """
                SELECT AVG(bonus::numeric) FROM clients                WHERE phone IS NOT NULL AND phone != ''
                AND bonus IS NOT NULL AND bonus > 0
            """
                )
            )

            max_bonus = await session.scalar(
                text(
                    """
                SELECT MAX(bonus::numeric) FROM clients                WHERE phone IS NOT NULL AND phone != ''
                AND bonus IS NOT NULL
            """
                )
            )

            min_bonus = await session.scalar(
                text(
                    """
                SELECT MIN(bonus::numeric) FROM clients                WHERE phone IS NOT NULL AND phone != ''
                AND bonus IS NOT NULL AND bonus > 0
            """
                )
            )

            print(f"   - Total clients with phones: {total_clients:,}")
            print(
                f"   - Clients with bonus > 0: {clients_with_bonus:,} ({clients_with_bonus/total_clients*100:.1f}%)"
            )
            print(
                f"   - Average bonus: {avg_bonus:.2f} UAH"
                if avg_bonus
                else "   - Average bonus: 0 UAH"
            )
            print(
                f"   - Maximum bonus: {max_bonus:.2f} UAH"
                if max_bonus
                else "   - Maximum bonus: 0 UAH"
            )
            print(
                f"   - Minimum bonus: {min_bonus:.2f} UAH"
                if min_bonus
                else "   - Minimum bonus: 0 UAH"
            )

            # Bonus distribution
            print("\n💳 Bonus distribution ranges:")
            result = await session.execute(
                text(
                    """
                SELECT
                    CASE
                        WHEN bonus::numeric = 0 THEN '0 UAH'
                        WHEN bonus::numeric > 0 AND bonus::numeric <= 50 THEN '1-50 UAH'
                        WHEN bonus::numeric > 50 AND bonus::numeric <= 100 THEN '51-100 UAH'
                        WHEN bonus::numeric > 100 AND bonus::numeric <= 500 THEN '101-500 UAH'
                        WHEN bonus::numeric > 500 AND bonus::numeric <= 1000 THEN '501-1000 UAH'
                        WHEN bonus::numeric > 1000 THEN '1000+ UAH'
                    END as bonus_range,
                    COUNT(*) as count
                FROM clients                WHERE phone IS NOT NULL AND phone != ''
                AND bonus IS NOT NULL
                GROUP BY
                    CASE
                        WHEN bonus::numeric = 0 THEN '0 UAH'
                        WHEN bonus::numeric > 0 AND bonus::numeric <= 50 THEN '1-50 UAH'
                        WHEN bonus::numeric > 50 AND bonus::numeric <= 100 THEN '51-100 UAH'
                        WHEN bonus::numeric > 100 AND bonus::numeric <= 500 THEN '101-500 UAH'
                        WHEN bonus::numeric > 500 AND bonus::numeric <= 1000 THEN '501-1000 UAH'
                        WHEN bonus::numeric > 1000 THEN '1000+ UAH'
                    END
                ORDER BY
                    CASE
                        WHEN bonus::numeric = 0 THEN 0
                        WHEN bonus::numeric > 0 AND bonus::numeric <= 50 THEN 1
                        WHEN bonus::numeric > 50 AND bonus::numeric <= 100 THEN 2
                        WHEN bonus::numeric > 100 AND bonus::numeric <= 500 THEN 3
                        WHEN bonus::numeric > 500 AND bonus::numeric <= 1000 THEN 4
                        WHEN bonus::numeric > 1000 THEN 5
                    END
            """
                )
            )

            for bonus_range, count in result.fetchall():
                print(f"   - {bonus_range}: {count:,} clients")

            # Top bonus holders
            print("\n🏆 Top 10 bonus holders:")
            result = await session.execute(
                text(
                    """
                SELECT
                    client_id,
                    firstname,
                    lastname,
                    phone,
                    bonus,
                    total_payed_sum
                FROM clients                WHERE phone IS NOT NULL AND phone != ''
                AND bonus IS NOT NULL AND bonus > 0
                ORDER BY bonus::numeric DESC
                LIMIT 10
            """
                )
            )

            for client_id, fname, lname, phone, bonus, total_paid in result.fetchall():
                name = f"{fname or ''} {lname or ''}".strip() or "N/A"
                print(
                    f"   {client_id}: {name} | {phone} | Bonus: {bonus} UAH | Total paid: {total_paid or 0} UAH"
                )

            # Check if we have transactions table
            print("\n🔄 Checking transactions relation:")

            try:
                # Check if transactions table exists
                table_exists = await session.scalar(
                    text(
                        """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'transactions'
                    )
                """
                    )
                )

                if table_exists:
                    print("   ✅ transactions table exists")

                    # Count transactions with bonus info
                    transactions_with_bonus = await session.scalar(
                        text(
                            """
                        SELECT COUNT(*) FROM transactions
                        WHERE bonus_accrued IS NOT NULL AND bonus_accrued > 0
                    """
                        )
                    )

                    transactions_with_bonus_used = await session.scalar(
                        text(
                            """
                        SELECT COUNT(*) FROM transactions
                        WHERE bonus_used IS NOT NULL AND bonus_used > 0
                    """
                        )
                    )

                    print(
                        f"   - Transactions with bonus accrued: {transactions_with_bonus:,}"
                    )
                    print(
                        f"   - Transactions with bonus used: {transactions_with_bonus_used:,}"
                    )

                    # Check correlation between client bonus and transactions
                    print("\n🔗 Bonus vs Transaction correlation:")

                    result = await session.execute(
                        text(
                            """
                        SELECT
                            c.client_id,
                            c.firstname,
                            c.lastname,
                            c.phone,
                            c.bonus as current_bonus,
                            COALESCE(SUM(t.bonus_accrued::numeric), 0) as total_accrued,
                            COALESCE(SUM(t.bonus_used::numeric), 0) as total_used,
                            COUNT(t.id) as transaction_count
                        FROM clients c
                        LEFT JOIN transactions t ON c.client_id = t.client_id
                        WHERE c.phone IS NOT NULL AND c.phone != ''
                        AND c.bonus IS NOT NULL AND c.bonus::numeric > 0
                        GROUP BY c.client_id, c.firstname, c.lastname, c.phone, c.bonus
                        ORDER BY c.bonus::numeric DESC
                        LIMIT 5
                    """
                        )
                    )

                    print("   Top 5 clients - bonus balance vs transactions:")
                    for (
                        client_id,
                        fname,
                        lname,
                        phone,
                        current_bonus,
                        accrued,
                        used,
                        tx_count,
                    ) in result.fetchall():
                        name = f"{fname or ''} {lname or ''}".strip() or "N/A"
                        calculated_bonus = float(accrued or 0) - float(used or 0)
                        print(f"     ID {client_id}: {name}")
                        print(f"       Current bonus: {current_bonus} UAH")
                        print(f"       Accrued: {accrued} UAH, Used: {used} UAH")
                        print(f"       Calculated: {calculated_bonus:.2f} UAH")
                        print(f"       Transactions: {tx_count}")
                        print(
                            f"       Match: {'✅' if abs(float(current_bonus) - calculated_bonus) < 0.01 else '❌'}"
                        )
                        print()

                else:
                    print("   ❌ transactions table not found")

            except Exception as e:
                print(f"   ⚠️ Error checking transactions: {e}")

            # Birthday bonus analysis
            print("\n🎂 Birthday bonus analysis:")

            birthday_bonus_clients = await session.scalar(
                text(
                    """
                SELECT COUNT(*) FROM clients                WHERE phone IS NOT NULL AND phone != ''
                AND birthday_bonus IS NOT NULL AND birthday_bonus > 0
            """
                )
            )

            avg_birthday_bonus = await session.scalar(
                text(
                    """
                SELECT AVG(birthday_bonus::numeric) FROM clients                WHERE phone IS NOT NULL AND phone != ''
                AND birthday_bonus IS NOT NULL and birthday_bonus > 0
            """
                )
            )

            print(f"   - Clients with birthday bonus: {birthday_bonus_clients:,}")
            print(
                f"   - Average birthday bonus: {avg_birthday_bonus:.2f} UAH"
                if avg_birthday_bonus
                else "   - Average birthday bonus: 0 UAH"
            )

            # Loyalty program analysis
            print("\n🎖️ Loyalty program analysis:")

            result = await session.execute(
                text(
                    """
                SELECT
                    loyalty_type,
                    COUNT(*) as count,
                    AVG(bonus::numeric) as avg_bonus
                FROM clients                WHERE phone IS NOT NULL AND phone != ''
                AND loyalty_type IS NOT NULL
                GROUP BY loyalty_type
                ORDER BY loyalty_type
            """
                )
            )

            print("   Loyalty types and average bonus:")
            for loyalty_type, count, avg_bonus in result.fetchall():
                print(
                    f"     Type {loyalty_type}: {count:,} clients, avg bonus: {avg_bonus:.2f} UAH"
                    if avg_bonus
                    else f"     Type {loyalty_type}: {count:,} clients, avg bonus: 0 UAH"
                )

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback

            traceback.print_exc()

        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(bonus_analysis())
