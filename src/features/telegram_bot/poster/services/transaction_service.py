"""
Poster transaction synchronization service
"""

import logging
from typing import List, Dict, Any

from .base_service import PosterBaseService
from ...models import Transaction, TransactionProduct
from ...schemas.transaction_product import TransactionProductFromPosterAPI
from ...schemas.transaction import TransactionFromPosterAPI

logger = logging.getLogger(__name__)


class TransactionService(PosterBaseService):
    """
    Service for synchronizing Poster transactions
    
    🚀 NEW: Uses PostgreSQL triggers for automatic discount calculation!
    No manual discount calculation needed - triggers handle it automatically
    when transaction_products are inserted/updated.
    """

    def sync_transactions_to_db(
        self, transactions: List[Dict[str, Any]], sync_products: bool = True
    ) -> Dict[str, int]:
        """
        Sync transactions to database with optimized batch processing

        Args:
            transactions: List of transaction data from API
            sync_products: Whether to also sync products from the "products" array
        """
        stats = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "errors": 0,
            "products_synced": 0,
        }

        if not transactions:
            return stats

        logger.info(f"Starting batch sync of {len(transactions)} transactions...")

        # 🚀 NEW: No need to pre-calculate discounts!
        # PostgreSQL triggers will calculate them automatically when products are inserted/updated
        logger.info("Using PostgreSQL triggers for automatic discount calculation...")

        with self.SessionLocal() as db:
            try:
                # Prepare lists for bulk operations
                new_transactions = []
                transaction_ids_to_check = [
                    int(t["transaction_id"]) for t in transactions
                ]

                # Get existing transactions in one query
                existing_transactions = (
                    db.query(Transaction)
                    .filter(Transaction.transaction_id.in_(transaction_ids_to_check))
                    .all()
                )
                existing_ids = {t.transaction_id: t for t in existing_transactions}

                # Get all client IDs that we need to check in one batch
                all_client_ids = set()
                for trans_data in transactions:
                    client_id = trans_data.get("client_id")
                    if client_id and client_id != 0:
                        all_client_ids.add(int(client_id))

                # Batch query for all clients at once
                existing_client_ids = set()
                if all_client_ids:
                    from ...models import Client

                    existing_clients = (
                        db.query(Client.client_id)
                        .filter(Client.client_id.in_(all_client_ids))
                        .all()
                    )
                    existing_client_ids = {c.client_id for c in existing_clients}

                logger.info(
                    f"Found {len(existing_ids)} existing transactions, {len(transactions) - len(existing_ids)} new"
                )
                logger.info(
                    f"Found {len(existing_client_ids)} existing clients out of {len(all_client_ids)} referenced"
                )

                # Process transactions
                for trans_data in transactions:
                    try:
                        stats["processed"] += 1
                        transaction_id = int(trans_data["transaction_id"])

                        if transaction_id in existing_ids:
                            # Update existing transaction using schema
                            try:
                                api_transaction = TransactionFromPosterAPI(**trans_data)
                                update_data = api_transaction.to_transaction_update(
                                    trans_data
                                )

                                # Get existing transaction and update it
                                existing_transaction = existing_ids[transaction_id]

                                # Simply update ALL fields - no complicated logic needed
                                for field, value in update_data.model_dump().items():
                                    if hasattr(existing_transaction, field):
                                        setattr(existing_transaction, field, value)

                                # Set client foreign key using batch-checked data
                                if (
                                    existing_transaction.client_id
                                    and existing_transaction.client_id
                                    in existing_client_ids
                                ):
                                    existing_transaction.client = (
                                        existing_transaction.client_id
                                    )
                                else:
                                    existing_transaction.client = None

                                # Parse dates manually (schema doesn't handle this)
                                existing_transaction.date_start = (
                                    self._parse_poster_datetime(
                                        trans_data.get("date_start")
                                    )
                                )
                                existing_transaction.date_close = (
                                    self._parse_poster_datetime(
                                        trans_data.get("date_close")
                                    )
                                )

                                # 🚀 No need to set discount manually - triggers will calculate it automatically!
                                # This happens when transaction_products are inserted/updated

                                stats["updated"] += 1

                            except Exception as e:
                                logger.error(
                                    f"Error updating transaction {transaction_id}: {e}"
                                )
                                stats["errors"] += 1
                        else:
                            # Create new transaction using schema
                            try:
                                api_transaction = TransactionFromPosterAPI(**trans_data)
                                transaction_create = (
                                    api_transaction.to_transaction_create(trans_data)
                                )

                                # Create SQLAlchemy model from validated data
                                transaction = Transaction(
                                    **transaction_create.model_dump()
                                )

                                # Set client foreign key using batch-checked data
                                if (
                                    transaction.client_id
                                    and transaction.client_id in existing_client_ids
                                ):
                                    transaction.client = transaction.client_id
                                else:
                                    transaction.client = None

                                # Parse dates manually (schema doesn't handle this)
                                transaction.date_start = self._parse_poster_datetime(
                                    trans_data.get("date_start")
                                )
                                transaction.date_close = self._parse_poster_datetime(
                                    trans_data.get("date_close")
                                )

                                # 🚀 No need to set discount manually - triggers will calculate it automatically!
                                # This happens when transaction_products are inserted/updated

                                new_transactions.append(transaction)
                                stats["created"] += 1

                            except Exception as e:
                                logger.error(
                                    f"Error creating transaction {transaction_id}: {e}"
                                )
                                stats["errors"] += 1

                    except Exception as e:
                        stats["errors"] += 1
                        logger.error(
                            f"Error processing transaction {trans_data.get('transaction_id')}: {e}"
                        )
                        continue

                # Bulk insert new transactions FIRST
                if new_transactions:
                    logger.info(
                        f"Bulk inserting {len(new_transactions)} new transactions..."
                    )
                    db.add_all(new_transactions)

                # Commit both new and updated transactions
                db.commit()
                logger.info(
                    f"Successfully processed {len(new_transactions)} new and {stats['updated']} updated transactions"
                )

                # Now sync products AFTER transactions are committed
                if sync_products:
                    logger.info("Starting bulk products sync for ALL transactions...")

                    # 🚀 STEP 1: Collect all unique product IDs for batch validation
                    all_product_ids = set()
                    for trans_data in transactions:
                        if "products" in trans_data:
                            for product_data in trans_data["products"]:
                                product_id = product_data.get("product_id")
                                if product_id:
                                    all_product_ids.add(int(product_id))

                    # 🚀 STEP 2: Batch query for existing products (single SQL query!)
                    existing_product_ids = set()
                    if all_product_ids:
                        from ...models.product import Product
                        existing_products = (
                            db.query(Product.poster_product_id)
                            .filter(Product.poster_product_id.in_(all_product_ids))
                            .all()
                        )
                        existing_product_ids = {p.poster_product_id for p in existing_products}
                        logger.info(f"Found {len(existing_product_ids)} existing products out of {len(all_product_ids)} referenced")

                    # 🚀 STEP 3: Create products with validated foreign keys
                    all_products = []
                    all_transaction_ids = []

                    for trans_data in transactions:
                        try:
                            transaction_id = int(trans_data["transaction_id"])

                            # Sync products for ALL transactions (existing and new)
                            if "products" in trans_data:
                                all_transaction_ids.append(transaction_id)
                                products_data = trans_data["products"]

                                for i, product_data in enumerate(products_data):
                                    try:
                                        # Use Pydantic schema for validation and conversion
                                        api_product = TransactionProductFromPosterAPI(
                                            **product_data
                                        )

                                        # Convert to TransactionProductCreate schema
                                        product_create = (
                                            api_product.to_transaction_product_create(
                                                transaction_id=transaction_id,
                                                position=i + 1,
                                            )
                                        )

                                        # 🚀 Set foreign key based on batch validation
                                        product_data_dict = product_create.model_dump()
                                        if product_create.poster_product_id and product_create.poster_product_id in existing_product_ids:
                                            product_data_dict['product'] = product_create.poster_product_id
                                        else:
                                            product_data_dict['product'] = None

                                        # Create SQLAlchemy model from validated data
                                        product = TransactionProduct(**product_data_dict)
                                        
                                        all_products.append(product)

                                    except Exception as e:
                                        logger.error(
                                            f"Error creating product {i+1} for transaction {transaction_id}: {e}"
                                        )
                                        continue

                        except Exception as e:
                            logger.error(
                                f"Error preparing products for transaction {trans_data.get('transaction_id')}: {e}"
                            )

                    # Bulk operations for all products at once
                    if all_transaction_ids:
                        # Single DELETE for all transactions in this batch
                        db.query(TransactionProduct).filter(
                            TransactionProduct.transaction_id.in_(all_transaction_ids)
                        ).delete()

                        # Single bulk INSERT for all products
                        if all_products:
                            logger.info(
                                f"Bulk inserting {len(all_products)} products for {len(all_transaction_ids)} transactions..."
                            )
                            
                            db.add_all(all_products)
                            stats["products_synced"] = len(all_products)

                # Final commit for products
                db.commit()
                
                logger.info(f"Batch sync completed: {stats}")

            except Exception as e:
                db.rollback()
                logger.error(f"Database error during batch sync: {e}")
                raise

        return stats
