"""
Corrected bonus analysis - dividing by 100 for proper UAH amounts
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


async def corrected_bonus_analysis():
    """Corrected bonus analysis with /100 for proper UAH amounts"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as session:
        try:
            print("💰 CORRECTED BONUS ANALYSIS (÷100 for UAH)")
            print("=" * 60)

            # Check raw vs corrected values
            print("\n🔍 Sample raw data vs corrected:")
            result = await session.execute(
                text(
                    """
                SELECT
                    client_id,
                    firstname,
                    lastname,
                    bonus as raw_bonus,
                    ROUND(bonus::numeric / 100, 2) as corrected_bonus,
                    total_payed_sum as raw_paid,
                    ROUND(total_payed_sum::numeric / 100, 2) as corrected_paid
                FROM clients                WHERE phone IS NOT NULL AND phone != ''
                AND bonus IS NOT NULL AND bonus::numeric > 0
                ORDER BY bonus::numeric DESC
                LIMIT 5
            """
                )
            )

            print("   Raw data vs Corrected (÷100):")
            for (
                client_id,
                fname,
                lname,
                raw_bonus,
                corrected_bonus,
                raw_paid,
                corrected_paid,
            ) in result.fetchall():
                name = f"{fname or ''} {lname or ''}".strip() or "N/A"
                print(f"   {client_id}: {name}")
                print(
                    f"      Raw bonus: {raw_bonus} → Corrected: {corrected_bonus} UAH"
                )
                print(f"      Raw paid: {raw_paid} → Corrected: {corrected_paid} UAH")
                print()

            # Corrected basic statistics
            print("\n📊 Corrected bonus statistics:")

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
                AND bonus IS NOT NULL AND bonus::numeric > 0
            """
                )
            )

            avg_bonus = await session.scalar(
                text(
                    """
                SELECT AVG(bonus::numeric / 100) FROM clients                WHERE phone IS NOT NULL AND phone != ''
                AND bonus IS NOT NULL AND bonus::numeric > 0
            """
                )
            )

            max_bonus = await session.scalar(
                text(
                    """
                SELECT MAX(bonus::numeric / 100) FROM clients                WHERE phone IS NOT NULL AND phone != ''
                AND bonus IS NOT NULL
            """
                )
            )

            total_bonus_amount = await session.scalar(
                text(
                    """
                SELECT SUM(bonus::numeric / 100) FROM clients                WHERE phone IS NOT NULL AND phone != ''
                AND bonus IS NOT NULL and bonus::numeric > 0
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
                f"   - Total bonus amount: {total_bonus_amount:,.2f} UAH"
                if total_bonus_amount
                else "   - Total bonus amount: 0 UAH"
            )

            # Corrected bonus distribution
            print("\n💳 Corrected bonus distribution:")

            zero_bonus = await session.scalar(
                text(
                    """
                SELECT COUNT(*) FROM clients                WHERE phone IS NOT NULL AND phone != ''
                AND (bonus IS NULL OR bonus::numeric = 0)
            """
                )
            )

            small_bonus = await session.scalar(
                text(
                    """
                SELECT COUNT(*) FROM clients                WHERE phone IS NOT NULL AND phone != ''
                AND bonus::numeric / 100 > 0 AND bonus::numeric / 100 <= 10
            """
                )
            )

            medium_bonus = await session.scalar(
                text(
                    """
                SELECT COUNT(*) FROM clients                WHERE phone IS NOT NULL AND phone != ''
                AND bonus::numeric / 100 > 10 AND bonus::numeric / 100 <= 100
            """
                )
            )

            large_bonus = await session.scalar(
                text(
                    """
                SELECT COUNT(*) FROM clients                WHERE phone IS NOT NULL AND phone != ''
                AND bonus::numeric / 100 > 100 AND bonus::numeric / 100 <= 1000
            """
                )
            )

            huge_bonus = await session.scalar(
                text(
                    """
                SELECT COUNT(*) FROM clients                WHERE phone IS NOT NULL AND phone != ''
                AND bonus::numeric / 100 > 1000
            """
                )
            )

            print(f"   - Zero bonus (0 UAH): {zero_bonus:,}")
            print(f"   - Small bonus (0.01-10 UAH): {small_bonus:,}")
            print(f"   - Medium bonus (10.01-100 UAH): {medium_bonus:,}")
            print(f"   - Large bonus (100.01-1000 UAH): {large_bonus:,}")
            print(f"   - Huge bonus (1000+ UAH): {huge_bonus:,}")

            # Top corrected bonus holders
            print("\n🏆 Top 10 bonus holders (corrected amounts):")
            result = await session.execute(
                text(
                    """
                SELECT
                    client_id,
                    firstname,
                    lastname,
                    phone,
                    ROUND(bonus::numeric / 100, 2) as corrected_bonus,
                    ROUND(total_payed_sum::numeric / 100, 2) as corrected_paid,
                    client_groups_name
                FROM clients                WHERE phone IS NOT NULL AND phone != ''
                AND bonus IS NOT NULL AND bonus::numeric > 0
                ORDER BY bonus::numeric DESC
                LIMIT 10
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
                cashback_percent = (
                    (bonus / total_paid * 100) if total_paid and total_paid > 0 else 0
                )
                print(f"   {client_id}: {name}")
                print(
                    f"      📞 {phone} | 💰 {bonus:.2f} UAH | 💳 Paid: {total_paid:.2f} UAH"
                )
                print(f"      👥 {group} | 📊 Cashback: {cashback_percent:.1f}%")
                print()

            # Check transactions with corrected amounts
            print("\n🔄 Transactions bonus analysis (corrected):")

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
                transactions_with_bonus = await session.scalar(
                    text(
                        """
                    SELECT COUNT(*) FROM transactions
                    WHERE bonus IS NOT NULL AND bonus::numeric > 0
                """
                    )
                )

                total_bonus_transactions = await session.scalar(
                    text(
                        """
                    SELECT SUM(bonus::numeric / 100) FROM transactions
                    WHERE bonus IS NOT NULL AND bonus::numeric > 0
                """
                    )
                )

                avg_bonus_per_transaction = await session.scalar(
                    text(
                        """
                    SELECT AVG(bonus::numeric / 100) FROM transactions
                    WHERE bonus IS NOT NULL AND bonus::numeric > 0
                """
                    )
                )

                print(f"   - Transactions with bonus: {transactions_with_bonus:,}")
                print(
                    f"   - Total bonus in transactions: {total_bonus_transactions:,.2f} UAH"
                    if total_bonus_transactions
                    else "   - Total bonus in transactions: 0 UAH"
                )
                print(
                    f"   - Average bonus per transaction: {avg_bonus_per_transaction:.2f} UAH"
                    if avg_bonus_per_transaction
                    else "   - Average bonus per transaction: 0 UAH"
                )

                # Recent bonus transactions
                print("\n📅 Recent bonus transactions (corrected amounts):")
                result = await session.execute(
                    text(
                        """
                    SELECT
                        transaction_id,
                        client_id,
                        ROUND(bonus::numeric / 100, 2) as corrected_bonus,
                        date_close,
                        ROUND(sum::numeric / 100, 2) as corrected_sum
                    FROM transactions
                    WHERE bonus IS NOT NULL AND bonus::numeric > 0
                    ORDER BY date_close DESC
                    LIMIT 5
                """
                    )
                )

                for (
                    tx_id,
                    client_id,
                    bonus,
                    date_close,
                    sum_amount,
                ) in result.fetchall():
                    bonus_percent = (
                        (bonus / sum_amount * 100)
                        if sum_amount and sum_amount > 0
                        else 0
                    )
                    print(
                        f"     TX {tx_id}: Client {client_id} | +{bonus:.2f} UAH bonus ({bonus_percent:.1f}%)"
                    )
                    print(f"       Purchase: {sum_amount:.2f} UAH | {date_close}")

            # Client groups with corrected averages
            print("\n🎖️ Client groups (corrected averages):")
            result = await session.execute(
                text(
                    """
                SELECT
                    client_groups_name,
                    COUNT(*) as clients_count,
                    ROUND(AVG(bonus::numeric / 100), 2) as avg_bonus,
                    ROUND(MAX(bonus::numeric / 100), 2) as max_bonus,
                    ROUND(AVG(total_payed_sum::numeric / 100), 2) as avg_paid
                FROM clients                WHERE phone IS NOT NULL AND phone != ''
                AND client_groups_name IS NOT NULL AND client_groups_name != ''
                GROUP BY client_groups_name
                ORDER BY avg_bonus DESC
            """
                )
            )

            for group_name, count, avg_bonus, max_bonus, avg_paid in result.fetchall():
                avg_cashback = (
                    (avg_bonus / avg_paid * 100) if avg_paid and avg_paid > 0 else 0
                )
                print(f"   - {group_name}: {count:,} clients")
                print(
                    f"     Avg bonus: {avg_bonus:.2f} UAH | Max: {max_bonus:.2f} UAH | Avg paid: {avg_paid:.2f} UAH"
                )
                print(f"     Avg cashback: {avg_cashback:.1f}%")
                print()

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback

            traceback.print_exc()

        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(corrected_bonus_analysis())
