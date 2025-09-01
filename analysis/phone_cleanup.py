"""
Phone number cleanup and normalization script
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


async def cleanup_phone_numbers():
    """Clean up and normalize problematic phone numbers"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as session:
        try:
            print("🧹 PHONE CLEANUP AND NORMALIZATION")
            print("=" * 50)

            # First, let's analyze the problematic phones in detail
            print("\n🔍 Analyzing problematic phone numbers:")

            result = await session.execute(
                text(
                    """
                SELECT
                    client_id,
                    phone,
                    phone_number,
                    firstname,
                    lastname,
                    country,
                    city
                FROM clients                WHERE phone IS NOT NULL
                AND phone != ''
                AND phone !~ '^\\+380 [0-9]{2} [0-9]{3} [0-9]{4}$'
            """
                )
            )

            problematic = result.fetchall()

            print(f"Found {len(problematic)} problematic phone numbers:")

            fixes = []
            for (
                client_id,
                phone,
                phone_number,
                firstname,
                lastname,
                country,
                city,
            ) in problematic:
                name = f"{firstname or ''} {lastname or ''}".strip()
                location = f"{city or ''}, {country or ''}".strip(", ")

                print(f"\n   📞 ID {client_id}: {name}")
                print(f"      Phone: '{phone}'")
                print(f"      Phone_number: '{phone_number}'")
                print(f"      Location: {location}")

                # Suggest fixes
                if phone.startswith("+49"):
                    # German number - mark as foreign
                    suggested_action = "MARK_AS_FOREIGN"
                    fix_note = "German number - keep as is, mark country"
                elif "+380 69" in phone and len(phone) == 17:
                    # Likely typo in operator code (699X instead of 69X)
                    clean_phone = phone.replace("+380 6990", "+380 699")
                    clean_phone_number = phone_number.replace("380699", "380699")
                    suggested_action = "FIX_OPERATOR_CODE"
                    fix_note = f"Fix operator code: {clean_phone}"
                elif "+380 65" in phone and len(phone) == 17:
                    # Likely typo in operator code (653X instead of 63X)
                    clean_phone = phone.replace("+380 6532", "+380 632")
                    clean_phone_number = phone_number.replace("380653", "380632")
                    suggested_action = "FIX_OPERATOR_CODE"
                    fix_note = f"Fix operator code: {clean_phone}"
                else:
                    suggested_action = "MANUAL_REVIEW"
                    fix_note = "Requires manual review"

                print(f"      Suggested: {suggested_action} - {fix_note}")

                fixes.append(
                    {
                        "client_id": client_id,
                        "current_phone": phone,
                        "current_phone_number": phone_number,
                        "action": suggested_action,
                        "note": fix_note,
                    }
                )

            # Phone operator statistics with corrections
            print(f"\n📊 Phone operator distribution after cleanup:")

            # Check for unknown operator codes
            result = await session.execute(
                text(
                    """
                SELECT
                    SUBSTRING(phone FROM '\\+380 ([0-9]{2})') as operator_code,
                    COUNT(*) as count
                FROM clients                WHERE phone LIKE '+380%'
                GROUP BY SUBSTRING(phone FROM '\\+380 ([0-9]{2})')
                ORDER BY count DESC
            """
                )
            )

            unknown_codes = []
            known_operators = {
                "39": "Kyivstar",
                "67": "Kyivstar",
                "68": "Kyivstar",
                "96": "Kyivstar",
                "97": "Kyivstar",
                "98": "Kyivstar",
                "50": "Vodafone",
                "66": "Vodafone",
                "95": "Vodafone",
                "99": "Vodafone",
                "63": "lifecell",
                "73": "lifecell",
                "93": "lifecell",
                "91": "3Mob",
                "92": "3Mob",
                "94": "3Mob",
            }

            print("\n   Operator code breakdown:")
            for code, count in result.fetchall():
                if code:
                    operator = known_operators.get(code, "❓ UNKNOWN")
                    if operator == "❓ UNKNOWN":
                        unknown_codes.append((code, count))
                    print(f"   - {code}: {count:,} phones ({operator})")

            if unknown_codes:
                print(f"\n⚠️ Unknown operator codes found:")
                for code, count in unknown_codes:
                    print(f"   - {code}: {count} phones (needs investigation)")

            # Quality metrics
            print(f"\n✅ Data quality metrics:")

            # Phone completeness
            total_clients = await session.scalar(text("SELECT COUNT(*) FROM clients"))
            with_phones = await session.scalar(
                text(
                    "SELECT COUNT(*) FROM clients WHERE phone IS NOT NULL AND phone != ''"
                )
            )
            completeness = (with_phones / total_clients) * 100

            print(
                f"   - Phone completeness: {completeness:.2f}% ({with_phones:,}/{total_clients:,})"
            )

            # Format consistency
            correct_format = await session.scalar(
                text(
                    """
                SELECT COUNT(*) FROM clients                WHERE phone ~ '^\\+380 [0-9]{2} [0-9]{3} [0-9]{4}$'
            """
                )
            )
            format_consistency = (correct_format / with_phones) * 100

            print(
                f"   - Format consistency: {format_consistency:.2f}% ({correct_format:,}/{with_phones:,})"
            )

            # Summary report
            print(f"\n📋 CLEANUP SUMMARY:")
            print(f"   - Total clients: {total_clients:,}")
            print(f"   - Clients with phones: {with_phones:,}")
            print(f"   - Problematic phones: {len(problematic)}")
            print(
                f"   - Automatic fixes possible: {sum(1 for f in fixes if f['action'] == 'FIX_OPERATOR_CODE')}"
            )
            print(
                f"   - Manual review needed: {sum(1 for f in fixes if f['action'] == 'MANUAL_REVIEW')}"
            )
            print(
                f"   - Foreign numbers: {sum(1 for f in fixes if f['action'] == 'MARK_AS_FOREIGN')}"
            )

            # Ask for confirmation to apply fixes
            print(
                f"\n🔧 Would you like to apply automatic fixes? (This will be handled separately)"
            )

        except Exception as e:
            print(f"❌ Error during cleanup analysis: {e}")

        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(cleanup_phone_numbers())
