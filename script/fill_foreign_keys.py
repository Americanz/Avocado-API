#!/usr/bin/env python3
"""
Script to fill foreign key fields for existing data
Updates transactions.spot and transaction_products.product fields
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from src.config.settings import settings


def fill_transaction_spot_foreign_keys():
    """Fill transactions.spot foreign key based on spot_id"""

    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        print("🔗 Filling transactions.spot foreign keys...")

        # Update transactions.spot = spot_id (direct mapping)
        result = conn.execute(
            text(
                """
            UPDATE transactions
            SET spot = spot_id
            WHERE spot IS NULL
        """
            )
        )

        print(f"✅ Updated {result.rowcount} transaction records with spot foreign key")
        conn.commit()


def fill_transaction_client_foreign_keys():
    """Fill transactions.client foreign key based on client_id"""

    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        print("🔗 Filling transactions.client foreign keys...")

        # Update transactions.client = client_id where client exists and client_id > 0
        result = conn.execute(
            text(
                """
            UPDATE transactions
            SET client = client_id
            WHERE client IS NULL
            AND client_id IS NOT NULL
            AND client_id > 0
            AND EXISTS (
                SELECT 1 FROM clients
                WHERE clients.client_id = transactions.client_id
            )
        """
            )
        )

        print(
            f"✅ Updated {result.rowcount} transaction records with client foreign key"
        )
        conn.commit()


def fill_transaction_product_foreign_keys():
    """Fill transaction_products.product foreign key based on poster_product_id"""

    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        print("🔗 Filling transaction_products.product foreign keys...")

        # Update transaction_products.product = poster_product_id where product exists
        result = conn.execute(
            text(
                """
            UPDATE transaction_products
            SET product = poster_product_id
            WHERE product IS NULL
            AND poster_product_id IS NOT NULL
            AND EXISTS (
                SELECT 1 FROM products
                WHERE products.poster_product_id = transaction_products.poster_product_id
            )
        """
            )
        )

        print(
            f"✅ Updated {result.rowcount} transaction product records with product foreign key"
        )
        conn.commit()


def check_data_stats():
    """Check current data statistics"""

    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        print("\n📊 Current data statistics:")

        # Transaction stats
        result = conn.execute(
            text(
                """
            SELECT
                COUNT(*) as total_transactions,
                COUNT(spot) as transactions_with_spot_fk,
                COUNT(*) - COUNT(spot) as transactions_without_spot_fk,
                COUNT(client) as transactions_with_client_fk,
                COUNT(CASE WHEN client_id > 0 THEN 1 END) as transactions_with_client_id
            FROM transactions
        """
            )
        )
        row = result.fetchone()
        print(f"   Transactions: {row[0]} total")
        print(f"   With spot FK: {row[1]}, without spot FK: {row[2]}")
        print(f"   With client FK: {row[3]}, with client_id > 0: {row[4]}")

        # Transaction products stats
        result = conn.execute(
            text(
                """
            SELECT
                COUNT(*) as total_products,
                COUNT(product) as products_with_fk,
                COUNT(*) - COUNT(product) as products_without_fk,
                COUNT(DISTINCT poster_product_id) as unique_poster_products
            FROM transaction_products
            WHERE poster_product_id IS NOT NULL
        """
            )
        )
        row = result.fetchone()
        print(
            f"   Transaction Products: {row[0]} total, {row[1]} with product FK, {row[2]} without product FK"
        )
        print(f"   Unique Poster Products: {row[3]}")

        # Products in catalog
        result = conn.execute(
            text(
                """
            SELECT COUNT(*) as total_products
            FROM products
        """
            )
        )
        row = result.fetchone()
        print(f"   Products in catalog: {row[0]}")

        # Clients
        result = conn.execute(
            text(
                """
            SELECT COUNT(*) as total_clients
            FROM clients
        """
            )
        )
        row = result.fetchone()
        print(f"   Clients: {row[0]}")

        # Spots
        result = conn.execute(
            text(
                """
            SELECT COUNT(*) as total_spots
            FROM spots
        """
            )
        )
        row = result.fetchone()
        print(f"   Spots: {row[0]}")


def main():
    """Main execution function"""

    print("🚀 Starting foreign key population script...")

    try:
        # Check current state
        check_data_stats()

        # Fill foreign keys
        fill_transaction_spot_foreign_keys()
        fill_transaction_client_foreign_keys()
        fill_transaction_product_foreign_keys()

        # Check final state
        print("\n📊 After updates:")
        check_data_stats()

        print("\n✅ Foreign key population completed successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
