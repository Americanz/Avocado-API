"""
Extended phone analysis - checking for duplicates and additional fields
"""

import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Import settings
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "ASYNC_DATABASE_URL",
    "postgresql+asyncpg://avocado_user:avocado_pass@localhost:5432/avocado_db",
)


async def extended_phone_analysis():
    """Extended analysis including duplicates and other fields"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as session:
        try:
            print("📱 EXTENDED PHONE ANALYSIS")
            print("=" * 50)

            # Check for duplicate phones
            print("\n🔄 Duplicate phone analysis:")
            result = await session.execute(
                text(
                    """
                SELECT phone, COUNT(*) as count
                FROM clients
                WHERE phone IS NOT NULL AND phone != ''
                GROUP BY phone
                HAVING COUNT(*) > 1
                ORDER BY count DESC
            """
                )
            )

            duplicates = result.fetchall()
            print(f"   - Duplicate phones found: {len(duplicates)}")

            if duplicates:
                print("\n📋 Top duplicate phones:")
                for phone, count in duplicates[:10]:
                    print(f"   - {phone}: {count} times")

                    # Show details for this phone
                    details = await session.execute(
                        text(
                            """
                        SELECT client_id, firstname, lastname, email, created_at
                        FROM clients
                        WHERE phone = :phone
                        ORDER BY created_at
                    """
                        ),
                        {"phone": phone},
                    )

                    for client_id, fname, lname, email, created in details.fetchall():
                        name = f"{fname or ''} {lname or ''}".strip() or "N/A"
                        print(
                            f"     → ID {client_id}: {name} | {email or 'No email'} | {created}"
                        )
                    print()

            # Check for empty emails with phones
            print("\n📧 Email analysis for phone users:")
            no_email_with_phone = await session.scalar(
                text(
                    """
                SELECT COUNT(*) FROM clients
                WHERE phone IS NOT NULL AND phone != ''
                AND (email IS NULL OR email = '')
            """
                )
            )

            total_with_phone = await session.scalar(
                text(
                    """
                SELECT COUNT(*) FROM clients
                WHERE phone IS NOT NULL AND phone != ''
            """
                )
            )

            print(
                f"   - Clients with phone but no email: {no_email_with_phone:,} ({no_email_with_phone/total_with_phone*100:.1f}%)"
            )
            print(
                f"   - Clients with both phone and email: {total_with_phone - no_email_with_phone:,} ({(total_with_phone - no_email_with_phone)/total_with_phone*100:.1f}%)"
            )

            # Address analysis
            print("\n🏠 Address information analysis:")

            with_address = await session.scalar(
                text(
                    """
                SELECT COUNT(*) FROM clients
                WHERE address IS NOT NULL AND address != ''
            """
                )
            )

            with_addresses_json = await session.scalar(
                text(
                    """
                SELECT COUNT(*) FROM clients
                WHERE addresses IS NOT NULL
                AND addresses::text != '[]'
                AND addresses::text != 'null'
            """
                )
            )

            print(f"   - Clients with address field: {with_address:,}")
            print(f"   - Clients with addresses JSON: {with_addresses_json:,}")

            # City analysis
            with_city = await session.scalar(
                text(
                    """
                SELECT COUNT(*) FROM clients
                WHERE city IS NOT NULL AND city != ''
            """
                )
            )
            print(f"   - Clients with city: {with_city:,}")

            if with_city > 0:
                print("\n🏙️ Top cities:")
                result = await session.execute(
                    text(
                        """
                    SELECT city, COUNT(*) as count
                    FROM clients
                    WHERE city IS NOT NULL AND city != ''
                    GROUP BY city
                    ORDER BY count DESC
                    LIMIT 10
                """
                    )
                )

                for city, count in result.fetchall():
                    print(f"   - {city}: {count:,} clients")

            # Birthday analysis
            print("\n🎂 Birthday analysis:")
            with_birthday = await session.scalar(
                text(
                    """
                SELECT COUNT(*) FROM clients
                WHERE birthday IS NOT NULL AND birthday != '' AND birthday != '0000-00-00'
            """
                )
            )
            print(f"   - Clients with valid birthday: {with_birthday:,}")

            # Gender analysis
            print("\n👥 Gender analysis:")
            result = await session.execute(
                text(
                    """
                SELECT
                    CASE
                        WHEN client_sex = '1' THEN 'Male'
                        WHEN client_sex = '2' THEN 'Female'
                        WHEN client_sex = '0' THEN 'Not specified'
                        ELSE 'Unknown'
                    END as gender,
                    COUNT(*) as count
                FROM clients                WHERE phone IS NOT NULL AND phone != ''
                GROUP BY client_sex
                ORDER BY count DESC
            """
                )
            )

            for gender, count in result.fetchall():
                print(f"   - {gender}: {count:,}")

            # Loyalty analysis
            print("\n💳 Loyalty and bonus analysis:")

            with_bonus = await session.scalar(
                text(
                    """
                SELECT COUNT(*) FROM clients
                WHERE phone IS NOT NULL AND phone != ''
                AND bonus IS NOT NULL AND bonus > 0
            """
                )
            )

            avg_bonus = await session.scalar(
                text(
                    """
                SELECT AVG(bonus) FROM clients
                WHERE phone IS NOT NULL AND phone != ''
                AND bonus IS NOT NULL AND bonus > 0
            """
                )
            )

            max_bonus = await session.scalar(
                text(
                    """
                SELECT MAX(bonus) FROM clients
                WHERE phone IS NOT NULL AND phone != ''
                AND bonus IS NOT NULL
            """
                )
            )

            print(f"   - Clients with bonuses > 0: {with_bonus:,}")
            print(
                f"   - Average bonus amount: {avg_bonus:.2f}"
                if avg_bonus
                else "   - Average bonus amount: 0"
            )
            print(
                f"   - Maximum bonus amount: {max_bonus}"
                if max_bonus
                else "   - Maximum bonus amount: 0"
            )

            # Total paid sum analysis
            total_payers = await session.scalar(
                text(
                    """
                SELECT COUNT(*) FROM clients
                WHERE phone IS NOT NULL AND phone != ''
                AND total_payed_sum IS NOT NULL AND total_payed_sum > 0
            """
                )
            )

            avg_paid = await session.scalar(
                text(
                    """
                SELECT AVG(total_payed_sum) FROM clients
                WHERE phone IS NOT NULL AND phone != ''
                AND total_payed_sum IS NOT NULL and total_payed_sum > 0
            """
                )
            )

            print(f"   - Clients with purchases: {total_payers:,}")
            print(
                f"   - Average total paid: {avg_paid:.2f} UAH"
                if avg_paid
                else "   - Average total paid: 0 UAH"
            )

        except Exception as e:
            print(f"❌ Error: {e}")

        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(extended_phone_analysis())
