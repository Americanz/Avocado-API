"""
Deep duplicate analysis for phone numbers
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


async def deep_duplicate_analysis():
    """Deep analysis of potential duplicates"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as session:
        try:
            print("🔍 DEEP DUPLICATE ANALYSIS")
            print("=" * 50)

            # Method 1: Direct phone duplicates
            print("\n📱 Method 1: Direct phone field duplicates")
            result = await session.execute(
                text(
                    """
                SELECT phone, COUNT(*) as count
                FROM clients
                WHERE phone IS NOT NULL AND phone != ''
                GROUP BY phone
                HAVING COUNT(*) > 1
                ORDER BY count DESC
                LIMIT 20
            """
                )
            )

            direct_duplicates = result.fetchall()
            print(f"   Direct phone duplicates: {len(direct_duplicates)}")

            # Method 2: phone_number field duplicates
            print("\n📞 Method 2: phone_number field duplicates")
            result = await session.execute(
                text(
                    """
                SELECT phone_number, COUNT(*) as count
                FROM clients
                WHERE phone_number IS NOT NULL AND phone_number != ''
                GROUP BY phone_number
                HAVING COUNT(*) > 1
                ORDER BY count DESC
                LIMIT 20
            """
                )
            )

            phone_number_duplicates = result.fetchall()
            print(f"   phone_number duplicates: {len(phone_number_duplicates)}")

            if phone_number_duplicates:
                print("\n📋 Sample phone_number duplicates:")
                for phone_num, count in phone_number_duplicates[:5]:
                    print(f"   - {phone_num}: {count} times")

                    # Show who has this phone_number
                    details = await session.execute(
                        text(
                            """
                        SELECT client_id, phone, firstname, lastname, created_at
                        FROM clients
                        WHERE phone_number = :phone_num
                        ORDER BY created_at
                    """
                        ),
                        {"phone_num": phone_num},
                    )

                    for client_id, phone, fname, lname, created in details.fetchall():
                        name = f"{fname or ''} {lname or ''}".strip() or "N/A"
                        print(f"     → ID {client_id}: {phone} | {name} | {created}")
                    print()

            # Method 3: Normalized phone duplicates (remove all non-digits except country code)
            print("\n🔧 Method 3: Normalized phone duplicates (digits only)")
            result = await session.execute(
                text(
                    """
                SELECT
                    REGEXP_REPLACE(phone, '[^0-9]', '', 'g') as normalized_phone,
                    COUNT(*) as count
                FROM clients
                WHERE phone IS NOT NULL AND phone != ''
                GROUP BY REGEXP_REPLACE(phone, '[^0-9]', '', 'g')
                HAVING COUNT(*) > 1
                ORDER BY count DESC
                LIMIT 20
            """
                )
            )

            normalized_duplicates = result.fetchall()
            print(f"   Normalized phone duplicates: {len(normalized_duplicates)}")

            if normalized_duplicates:
                print("\n📋 Sample normalized duplicates:")
                for norm_phone, count in normalized_duplicates[:5]:
                    print(f"   - {norm_phone}: {count} times")

                    # Show original phones for this normalized version
                    details = await session.execute(
                        text(
                            """
                        SELECT client_id, phone, firstname, lastname
                        FROM clients
                        WHERE REGEXP_REPLACE(phone, '[^0-9]', '', 'g') = :norm_phone
                        ORDER BY client_id
                    """
                        ),
                        {"norm_phone": norm_phone},
                    )

                    for client_id, phone, fname, lname in details.fetchall():
                        name = f"{fname or ''} {lname or ''}".strip() or "N/A"
                        print(f"     → ID {client_id}: '{phone}' | {name}")
                    print()

            # Method 4: Similar names with same phones
            print("\n👥 Method 4: Same firstname+lastname combinations")
            result = await session.execute(
                text(
                    """
                SELECT
                    LOWER(TRIM(firstname)) as first,
                    LOWER(TRIM(lastname)) as last,
                    COUNT(*) as count
                FROM clients
                WHERE phone IS NOT NULL AND phone != ''
                AND firstname IS NOT NULL AND firstname != ''
                AND lastname IS NOT NULL AND lastname != ''
                GROUP BY LOWER(TRIM(firstname)), LOWER(TRIM(lastname))
                HAVING COUNT(*) > 1
                ORDER BY count DESC
                LIMIT 10
            """
                )
            )

            name_duplicates = result.fetchall()
            print(f"   Same name combinations: {len(name_duplicates)}")

            if name_duplicates:
                print("\n📋 Sample name duplicates:")
                for first, last, count in name_duplicates[:3]:
                    print(f"   - {first.title()} {last.title()}: {count} times")

                    # Show these people with their phones
                    details = await session.execute(
                        text(
                            """
                        SELECT client_id, phone, firstname, lastname, email
                        FROM clients
                        WHERE LOWER(TRIM(firstname)) = :first
                        AND LOWER(TRIM(lastname)) = :last
                        AND phone IS NOT NULL AND phone != ''
                        ORDER BY client_id
                    """
                        ),
                        {"first": first, "last": last},
                    )

                    for client_id, phone, fname, lname, email in details.fetchall():
                        print(f"     → ID {client_id}: {phone} | {email or 'No email'}")
                    print()

            # Method 5: Check for potential phone format variations
            print("\n🔀 Method 5: Phone format variations check")

            # Find phones that might be the same but formatted differently
            result = await session.execute(
                text(
                    """
                WITH phone_digits AS (
                    SELECT
                        client_id,
                        phone,
                        REGEXP_REPLACE(phone, '[^0-9]', '', 'g') as digits_only
                    FROM clients
                    WHERE phone IS NOT NULL AND phone != ''
                ),
                digit_counts AS (
                    SELECT digits_only, COUNT(*) as count
                    FROM phone_digits
                    GROUP BY digits_only
                    HAVING COUNT(*) > 1
                )
                SELECT COUNT(*) FROM digit_counts
            """
                )
            )

            format_variations = result.scalar()
            print(f"   Potential format variations: {format_variations}")

            # Sample some random phones to see patterns
            print("\n📊 Method 6: Random sample analysis")
            result = await session.execute(
                text(
                    """
                SELECT phone, phone_number, client_id
                FROM clients
                WHERE phone IS NOT NULL AND phone != ''
                ORDER BY RANDOM()
                LIMIT 10
            """
                )
            )

            print("   Random phone samples:")
            for phone, phone_number, client_id in result.fetchall():
                print(f"     ID {client_id}: '{phone}' → '{phone_number}'")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback

            traceback.print_exc()

        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(deep_duplicate_analysis())
