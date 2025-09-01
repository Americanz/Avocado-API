"""
Detailed phone number analysis for clients"""

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


async def detailed_phone_analysis():
    """Detailed analysis of phone number patterns and quality"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as session:
        try:
            print("📱 DETAILED PHONE ANALYSIS")
            print("=" * 50)

            # Phone operator analysis
            print("\n🏢 Ukrainian mobile operators analysis:")

            operators = [
                ("Kyivstar", "39", "67", "68", "96", "97", "98"),
                ("Vodafone", "50", "66", "95", "99"),
                ("lifecell", "63", "73", "93"),
                ("3Mob/PEOPLEnet", "91", "92", "94"),
                ("Other", ""),
            ]

            for name, *codes in operators:
                if name == "Other":
                    # Count phones that don't match known operators
                    query = """
                        SELECT COUNT(*) FROM clients                        WHERE phone LIKE '+380%'
                        AND phone NOT LIKE '+380 39%'
                        AND phone NOT LIKE '+380 50%'
                        AND phone NOT LIKE '+380 63%'
                        AND phone NOT LIKE '+380 66%'
                        AND phone NOT LIKE '+380 67%'
                        AND phone NOT LIKE '+380 68%'
                        AND phone NOT LIKE '+380 73%'
                        AND phone NOT LIKE '+380 91%'
                        AND phone NOT LIKE '+380 92%'
                        AND phone NOT LIKE '+380 93%'
                        AND phone NOT LIKE '+380 94%'
                        AND phone NOT LIKE '+380 95%'
                        AND phone NOT LIKE '+380 96%'
                        AND phone NOT LIKE '+380 97%'
                        AND phone NOT LIKE '+380 98%'
                        AND phone NOT LIKE '+380 99%'
                    """
                    count = await session.scalar(text(query))
                else:
                    # Count for specific operator codes
                    conditions = " OR ".join(
                        [f"phone LIKE '+380 {code}%'" for code in codes]
                    )
                    query = f"SELECT COUNT(*) FROM clients WHERE {conditions}"
                    count = await session.scalar(text(query))

                print(f"   - {name}: {count:,}")

            # Phone length analysis
            print("\n📏 Phone length analysis:")
            result = await session.execute(
                text(
                    """
                SELECT
                    LENGTH(phone) as phone_length,
                    COUNT(*) as count
                FROM clients                WHERE phone IS NOT NULL AND phone != ''
                GROUP BY LENGTH(phone)
                ORDER BY phone_length
            """
                )
            )

            for length, count in result.fetchall():
                print(f"   - Length {length}: {count:,} phones")

            # Validation checks
            print("\n✅ Phone validation checks:")

            # Correct format check
            correct_format = await session.scalar(
                text(
                    """
                SELECT COUNT(*) FROM clients                WHERE phone ~ '^\+380 [0-9]{2} [0-9]{3} [0-9]{4}$'
            """
                )
            )
            print(f"   - Correct format (+380 XX XXX XXXX): {correct_format:,}")

            # Invalid formats
            invalid_format = await session.scalar(
                text(
                    """
                SELECT COUNT(*) FROM clients                WHERE phone IS NOT NULL
                AND phone != ''
                AND phone !~ '^\+380 [0-9]{2} [0-9]{3} [0-9]{4}$'
            """
                )
            )
            print(f"   - Invalid format: {invalid_format:,}")

            if invalid_format > 0:
                print("\n❌ Sample invalid phone numbers:")
                result = await session.execute(
                    text(
                        """
                    SELECT phone, phone_number, client_id, firstname, lastname
                    FROM clients                    WHERE phone IS NOT NULL
                    AND phone != ''
                    AND phone !~ '^\+380 [0-9]{2} [0-9]{3} [0-9]{4}$'
                    LIMIT 10
                """
                    )
                )

                for (
                    phone,
                    phone_number,
                    client_id,
                    firstname,
                    lastname,
                ) in result.fetchall():
                    name = f"{firstname or ''} {lastname or ''}".strip()
                    print(f"     ID {client_id}: '{phone}' | '{phone_number}' | {name}")

            # Phone_number validation
            print("\n🔢 Phone_number field analysis:")

            correct_phone_number = await session.scalar(
                text(
                    """
                SELECT COUNT(*) FROM clients                WHERE phone_number ~ '^380[0-9]{9}$'
            """
                )
            )
            print(
                f"   - Correct phone_number format (380XXXXXXXXX): {correct_phone_number:,}"
            )

            # Missing phone_number
            missing_phone_number = await session.scalar(
                text(
                    """
                SELECT COUNT(*) FROM clients                WHERE phone IS NOT NULL AND phone != ''
                AND (phone_number IS NULL OR phone_number = '')
            """
                )
            )
            print(f"   - Missing phone_number: {missing_phone_number:,}")

            # Mismatched phone vs phone_number
            print("\n🔄 Phone vs phone_number consistency:")
            result = await session.execute(
                text(
                    """
                SELECT COUNT(*) FROM clients                WHERE phone IS NOT NULL AND phone != ''
                AND phone_number IS NOT NULL AND phone_number != ''
                AND REPLACE(REPLACE(phone, '+', ''), ' ', '') != phone_number
            """
                )
            )
            mismatched = result.scalar()
            print(f"   - Mismatched phone/phone_number: {mismatched:,}")

            if mismatched > 0:
                print("\n⚠️ Sample mismatched records:")
                result = await session.execute(
                    text(
                        """
                    SELECT phone, phone_number, client_id, firstname, lastname
                    FROM clients                    WHERE phone IS NOT NULL AND phone != ''
                    AND phone_number IS NOT NULL AND phone_number != ''
                    AND REPLACE(REPLACE(phone, '+', ''), ' ', '') != phone_number
                    LIMIT 5
                """
                    )
                )

                for (
                    phone,
                    phone_number,
                    client_id,
                    firstname,
                    lastname,
                ) in result.fetchall():
                    name = f"{firstname or ''} {lastname or ''}".strip()
                    expected = phone.replace("+", "").replace(" ", "")
                    print(
                        f"     ID {client_id}: phone='{phone}' -> expected='{expected}' but got='{phone_number}' | {name}"
                    )

            # Recent phone registrations
            print("\n📅 Recent phone registrations (last 20):")
            result = await session.execute(
                text(
                    """
                SELECT phone, firstname, lastname, created_at, client_id
                FROM clients                WHERE phone IS NOT NULL AND phone != ''
                ORDER BY created_at DESC
                LIMIT 20
            """
                )
            )

            for phone, firstname, lastname, created_at, client_id in result.fetchall():
                name = f"{firstname or ''} {lastname or ''}".strip() or "N/A"
                print(f"   {created_at}: {phone} | {name} (ID: {client_id})")

        except Exception as e:
            print(f"❌ Error: {e}")

        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(detailed_phone_analysis())
