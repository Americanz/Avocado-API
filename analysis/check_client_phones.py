"""
Script to analyze clients table and check phone numbers
"""

import asyncio
import sys
import os
from sqlalchemy import text, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import settings directly
from dotenv import load_dotenv

load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv(
    "ASYNC_DATABASE_URL",
    "postgresql+asyncpg://avocado_user:avocado_pass@localhost:5432/avocado_db",
)


async def analyze_clients():
    """Analyze clients table and phone numbers"""

    # Create database connection
    engine = create_async_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as session:
        try:
            print("🔍 Analyzing clients table...")

            # Basic table info
            total_count = await session.scalar(text("SELECT COUNT(*) FROM clients"))
            print(f"📊 Total clients in table: {total_count}")

            if total_count == 0:
                print("❌ No clients found in clients table")
                return

            # Phone analysis
            print("\n📱 Phone number analysis:")

            # Clients with phones
            with_phone = await session.scalar(
                text(
                    "SELECT COUNT(*) FROM clients WHERE phone IS NOT NULL AND phone != ''"
                )
            )
            print(f"   - Clients with phone: {with_phone}")

            # Clients without phones
            without_phone = await session.scalar(
                text("SELECT COUNT(*) FROM clients WHERE phone IS NULL OR phone = ''")
            )
            print(f"   - Clients without phone: {without_phone}")

            # Phone format analysis
            print("\n📋 Phone format analysis:")

            # Ukrainian phones (+380)
            ua_phones = await session.scalar(
                text("SELECT COUNT(*) FROM clients WHERE phone LIKE '+380%'")
            )
            print(f"   - Ukrainian (+380): {ua_phones}")

            # Other international phones
            intl_phones = await session.scalar(
                text(
                    "SELECT COUNT(*) FROM clients WHERE phone LIKE '+%' AND phone NOT LIKE '+380%'"
                )
            )
            print(f"   - Other international (+): {intl_phones}")

            # Local format phones
            local_phones = await session.scalar(
                text(
                    "SELECT COUNT(*) FROM clients WHERE phone NOT LIKE '+%' AND phone IS NOT NULL AND phone != ''"
                )
            )
            print(f"   - Local format (no +): {local_phones}")

            # Sample phones
            print("\n📞 Sample phone numbers:")
            result = await session.execute(
                text(
                    "SELECT phone, phone_number FROM clients WHERE phone IS NOT NULL AND phone != '' LIMIT 10"
                )
            )
            samples = result.fetchall()

            for i, (phone, phone_number) in enumerate(samples, 1):
                print(f"   {i}. phone: '{phone}' | phone_number: '{phone_number}'")

            # ID range analysis
            print("\n🆔 Client ID analysis:")
            min_id = await session.scalar(text("SELECT MIN(client_id) FROM clients"))
            max_id = await session.scalar(text("SELECT MAX(client_id) FROM clients"))
            print(f"   - ID range: {min_id} - {max_id}")

            # Recent clients
            print("\n🕒 Recent clients (last 10 by client_id):")
            result = await session.execute(
                text(
                    """
                    SELECT client_id, firstname, lastname, phone, created_at
                    FROM clients                    ORDER BY client_id DESC
                    LIMIT 10
                """
                )
            )
            recent = result.fetchall()

            for client in recent:
                poster_id, firstname, lastname, phone, created_at = client
                name = f"{firstname or ''} {lastname or ''}".strip()
                print(f"   - ID {poster_id}: {name} | {phone} | {created_at}")

            # Duplicates analysis
            print("\n🔍 Duplicate analysis:")
            result = await session.execute(
                text(
                    """
                    SELECT phone, COUNT(*) as count
                    FROM clients                    WHERE phone IS NOT NULL AND phone != ''
                    GROUP BY phone
                    HAVING COUNT(*) > 1
                    ORDER BY count DESC
                    LIMIT 5
                """
                )
            )
            duplicates = result.fetchall()

            if duplicates:
                print("   - Duplicate phones found:")
                for phone, count in duplicates:
                    print(f"     {phone}: {count} times")
            else:
                print("   - No duplicate phones found")

        except Exception as e:
            print(f"❌ Error analyzing database: {e}")

        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(analyze_clients())
