"""
Simple bonus analysis - fixed version
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


async def simple_bonus_analysis():
    """Simple bonus analysis without complex grouping"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as session:
        try:
            print("💰 BONUS ANALYSIS - PART 2")
            print("=" * 50)

            # Simple bonus ranges
            print("\n💳 Bonus distribution:")

            zero_bonus = await session.scalar(
                text(
                    """
                SELECT COUNT(*) FROM clients
                WHERE phone IS NOT NULL AND phone != ''
                AND (bonus IS NULL OR bonus::numeric = 0)
            """
                )
            )

            small_bonus = await session.scalar(
                text(
                    """
                SELECT COUNT(*) FROM clients
                WHERE phone IS NOT NULL AND phone != ''
                AND bonus::numeric > 0 AND bonus::numeric <= 100
            """
                )
            )

            medium_bonus = await session.scalar(
                text(
                    """
                SELECT COUNT(*) FROM clients
                WHERE phone IS NOT NULL AND phone != ''
                AND bonus::numeric > 100 AND bonus::numeric <= 1000
            """
                )
            )

            large_bonus = await session.scalar(
                text(
                    """
                SELECT COUNT(*) FROM clients
                WHERE phone IS NOT NULL AND phone != ''
                AND bonus::numeric > 1000 AND bonus::numeric <= 10000
            """
                )
            )

            huge_bonus = await session.scalar(
                text(
                    """
                SELECT COUNT(*) FROM clients
                WHERE phone IS NOT NULL AND phone != ''
                AND bonus::numeric > 10000
            """
                )
            )

            print(f"   - Zero bonus (0 UAH): {zero_bonus:,}")
            print(f"   - Small bonus (1-100 UAH): {small_bonus:,}")
            print(f"   - Medium bonus (101-1000 UAH): {medium_bonus:,}")
            print(f"   - Large bonus (1001-10000 UAH): {large_bonus:,}")
            print(f"   - Huge bonus (10000+ UAH): {huge_bonus:,}")

            # Top bonus holders
            print("\n🏆 Top 15 bonus holders:")
            result = await session.execute(
                text(
                    """
                SELECT
                    client_id,
                    firstname,
                    lastname,
                    phone,
                    bonus,
                    total_payed_sum,
                    client_groups_name
                FROM clients
                WHERE phone IS NOT NULL AND phone != ''
                AND bonus IS NOT NULL AND bonus::numeric > 0
                ORDER BY bonus::numeric DESC
                LIMIT 15
            """
                )
            )

            for (
                client_id,
                fname,
                lname,
                phone,
                bonus,
                total_paid,
                group_name,
            ) in result.fetchall():
                name = f"{fname or ''} {lname or ''}".strip() or "N/A"
                group = group_name or "No group"
                print(f"   {client_id}: {name}")
                print(
                    f"      📞 {phone} | 💰 {bonus} UAH | 💳 Paid: {total_paid or 0} UAH | 👥 {group}"
                )

            # Check transactions table relation
            print("\n🔄 Checking transactions table:")

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

                # Check bonus fields in transactions
                columns = await session.execute(
                    text(
                        """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'transactions'
                    AND column_name LIKE '%bonus%'
                """
                    )
                )

                bonus_columns = [row[0] for row in columns.fetchall()]
                print(f"   📋 Bonus-related columns: {bonus_columns}")

                if bonus_columns:
                    # Count transactions with bonus activity
                    for col in bonus_columns:
                        count = await session.scalar(
                            text(
                                f"""
                            SELECT COUNT(*) FROM transactions
                            WHERE {col} IS NOT NULL AND {col}::numeric > 0
                        """
                            )
                        )

                        total_amount = await session.scalar(
                            text(
                                f"""
                            SELECT SUM({col}::numeric) FROM transactions
                            WHERE {col} IS NOT NULL AND {col}::numeric > 0
                        """
                            )
                        )

                        print(
                            f"   - {col}: {count:,} transactions, total: {total_amount:.2f} UAH"
                            if total_amount
                            else f"   - {col}: {count:,} transactions"
                        )

                # Recent bonus activity in transactions
                if "bonus_accrued" in bonus_columns:
                    print("\n📅 Recent bonus accrual (last 10 transactions):")
                    result = await session.execute(
                        text(
                            """
                        SELECT
                            poster_transaction_id,
                            client_id,
                            bonus_accrued,
                            date_close_date,
                            products_sum
                        FROM transactions
                        WHERE bonus_accrued IS NOT NULL AND bonus_accrued::numeric > 0
                        ORDER BY date_close_date DESC
                        LIMIT 10
                    """
                        )
                    )

                    for (
                        tx_id,
                        client_id,
                        bonus_accrued,
                        date_close,
                        products_sum,
                    ) in result.fetchall():
                        print(
                            f"     TX {tx_id}: Client {client_id} | +{bonus_accrued} bonus | {products_sum} UAH | {date_close}"
                        )

            else:
                print("   ❌ transactions table not found")

            # Birthday bonus analysis
            print("\n🎂 Birthday bonus analysis:")

            birthday_bonus_clients = await session.scalar(
                text(
                    """
                SELECT COUNT(*) FROM clients
                WHERE phone IS NOT NULL AND phone != ''
                AND birthday_bonus IS NOT NULL AND birthday_bonus::numeric > 0
            """
                )
            )

            total_birthday_bonus = await session.scalar(
                text(
                    """
                SELECT SUM(birthday_bonus::numeric) FROM clients
                WHERE phone IS NOT NULL AND phone != ''
                AND birthday_bonus IS NOT NULL and birthday_bonus::numeric > 0
            """
                )
            )

            print(f"   - Clients with birthday bonus > 0: {birthday_bonus_clients:,}")
            print(
                f"   - Total birthday bonus amount: {total_birthday_bonus:.2f} UAH"
                if total_birthday_bonus
                else "   - Total birthday bonus amount: 0 UAH"
            )

            # Loyalty groups vs bonus
            print("\n🎖️ Client groups and average bonus:")
            result = await session.execute(
                text(
                    """
                SELECT
                    client_groups_name,
                    COUNT(*) as clients_count,
                    AVG(bonus::numeric) as avg_bonus,
                    MAX(bonus::numeric) as max_bonus
                FROM clients
                WHERE phone IS NOT NULL AND phone != ''
                AND client_groups_name IS NOT NULL AND client_groups_name != ''
                GROUP BY client_groups_name
                ORDER BY avg_bonus DESC
            """
                )
            )

            for group_name, count, avg_bonus, max_bonus in result.fetchall():
                print(
                    f"   - {group_name}: {count:,} clients | Avg: {avg_bonus:.2f} UAH | Max: {max_bonus:.2f} UAH"
                )

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback

            traceback.print_exc()

        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(simple_bonus_analysis())
