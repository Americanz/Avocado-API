"""
Check transactions table structure
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


async def check_transactions_structure():
    """Check the structure of transactions table"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as session:
        try:
            print("🔍 CHECKING transactions TABLE STRUCTURE")
            print("=" * 60)

            # Check if table exists
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

            if not table_exists:
                print("❌ transactions table does not exist")
                return

            print("✅ transactions table exists")

            # Get all columns
            print("\n📋 Table columns:")
            result = await session.execute(
                text(
                    """
                SELECT
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_name = 'transactions'
                ORDER BY ordinal_position
            """
                )
            )

            columns = result.fetchall()
            for col_name, data_type, is_nullable, default in columns:
                nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
                default_str = f" DEFAULT {default}" if default else ""
                print(f"   - {col_name}: {data_type} {nullable}{default_str}")

            # Check for ID column variations
            print("\n🔑 Possible ID columns:")
            id_columns = [col[0] for col in columns if "id" in col[0].lower()]
            for col in id_columns:
                print(f"   - {col}")

            # Check sample data
            print("\n📊 Sample data (first 3 rows):")
            try:
                # Try to get sample data with common column names
                common_columns = [
                    "id",
                    "transaction_id",
                    "client_id",
                    "bonus",
                    "products_sum",
                    "date_close_date",
                ]
                existing_columns = [col[0] for col in columns]

                # Find which columns exist
                select_columns = []
                for col in common_columns:
                    if col in existing_columns:
                        select_columns.append(col)

                if select_columns:
                    select_query = (
                        f"SELECT {', '.join(select_columns)} FROM transactions LIMIT 3"
                    )
                    result = await session.execute(text(select_query))

                    for row in result.fetchall():
                        print(f"   {dict(zip(select_columns, row))}")
                else:
                    print("   No common columns found for sample")

            except Exception as e:
                print(f"   Error getting sample data: {e}")

            # Check bonus-related columns specifically
            print("\n💰 Bonus-related columns:")
            bonus_cols = [col[0] for col in columns if "bonus" in col[0].lower()]
            for col in bonus_cols:
                # Count non-null values
                count = await session.scalar(
                    text(f"SELECT COUNT(*) FROM transactions WHERE {col} IS NOT NULL")
                )
                print(f"   - {col}: {count:,} non-null values")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback

            traceback.print_exc()

        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_transactions_structure())
