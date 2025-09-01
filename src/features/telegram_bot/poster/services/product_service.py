"""
Poster product synchronization service
"""

import logging
from typing import List, Dict, Any
from sqlalchemy import func
from .base_service import PosterBaseService
from ...models import Product

logger = logging.getLogger(__name__)


class ProductService(PosterBaseService):
    """Service for synchronizing Poster products"""

    def sync_products_to_db(self, products: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Sync products to database with optimized batch processing

        Args:
            products: List of product data from API

        Returns:
            Dict with sync statistics
        """
        stats = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "errors": 0,
        }

        if not products:
            logger.info("No products to sync")
            return stats

        logger.info(f"Starting mega-batch sync of {len(products)} products...")

        with self.SessionLocal() as db:
            try:
                # Get existing products in one query
                product_ids_to_check = [int(p["product_id"]) for p in products]
                existing_products_query = (
                    db.query(Product.poster_product_id, Product.updated_at)
                    .filter(Product.poster_product_id.in_(product_ids_to_check))
                    .all()
                )

                existing_products = {
                    row.poster_product_id: row.updated_at
                    for row in existing_products_query
                }

                logger.info(
                    f"Found {len(existing_products)} existing products, {len(products) - len(existing_products)} new"
                )

                # Separate new and updated products
                new_products = []
                products_to_update = []

                for product_data in products:
                    try:
                        stats["processed"] += 1
                        product_id = int(product_data["product_id"])

                        if product_id in existing_products:
                            # Check if update is needed
                            existing_updated_at = existing_products[product_id]
                            api_updated_at = self._parse_poster_datetime(
                                product_data.get("updated_at")
                            )

                            if (
                                api_updated_at
                                and existing_updated_at
                                and api_updated_at > existing_updated_at
                            ):
                                # Prepare for bulk update
                                update_data = self._prepare_product_update_data(
                                    product_data
                                )
                                update_data["poster_product_id"] = product_id
                                products_to_update.append(update_data)
                                stats["updated"] += 1
                            # else: Product is up to date, skip
                        else:
                            # New product
                            product = self._create_product(product_data)
                            new_products.append(product)
                            stats["created"] += 1

                    except Exception as e:
                        stats["errors"] += 1
                        logger.error(
                            f"Error processing product {product_data.get('product_id')}: {e}"
                        )
                        continue

                # Bulk insert new products
                if new_products:
                    logger.info(f"Bulk inserting {len(new_products)} new products...")
                    db.add_all(new_products)

                # Bulk update existing products
                if products_to_update:
                    logger.info(f"Bulk updating {len(products_to_update)} products...")
                    db.bulk_update_mappings(Product, products_to_update)

                db.commit()
                logger.info(f"Mega-batch products sync completed: {stats}")

            except Exception as e:
                db.rollback()
                logger.error(f"Database error during products sync: {e}")
                raise

        return stats

    def _prepare_product_update_data(
        self, product_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare product data for bulk update"""
        # Parse datetime fields
        updated_at = self._parse_poster_datetime(product_data.get("updated_at"))

        return {
            "product_name": product_data.get("product_name"),
            "product_code": product_data.get("product_code"),
            "barcode": product_data.get("barcode"),
            "category_name": product_data.get("category_name"),
            "menu_category_id": self._safe_int(product_data.get("menu_category_id")),
            "unit": product_data.get("unit"),
            "cost": self._safe_decimal(product_data.get("cost")),
            "cost_netto": self._safe_decimal(product_data.get("cost_netto")),
            "weight_flag": bool(product_data.get("weight_flag", False)),
            "type": self._safe_int(product_data.get("type")),
            "color": product_data.get("color"),
            "photo": product_data.get("photo"),
            "photo_origin": product_data.get("photo_origin"),
            "sort_order": self._safe_int(product_data.get("sort_order")),
            "tax_id": self._safe_int(product_data.get("tax_id")),
            "product_tax_id": self._safe_int(product_data.get("product_tax_id")),
            "fiscal": bool(product_data.get("fiscal", False)),
            "fiscal_code": product_data.get("fiscal_code"),
            "workshop": self._safe_int(product_data.get("workshop")),
            "nodiscount": bool(product_data.get("nodiscount", False)),
            "ingredient_id": self._safe_int(product_data.get("ingredient_id")),
            "cooking_time": self._safe_int(product_data.get("cooking_time")),
            "out": self._safe_int(product_data.get("out")),
            "spots": product_data.get("spots"),
            "sources": product_data.get("sources"),
            "modifications": product_data.get("modifications"),
            "ingredients": product_data.get("ingredients"),
            "updated_at": updated_at,
            "raw_data": product_data,
        }

    def _create_product(self, product_data: Dict[str, Any]) -> Product:
        """Create Product from API data"""
        # Parse datetime fields
        updated_at = self._parse_poster_datetime(product_data.get("updated_at"))

        return Product(
            poster_product_id=int(product_data["product_id"]),
            product_name=product_data.get("product_name"),
            product_code=product_data.get("product_code"),
            barcode=product_data.get("barcode"),
            category_name=product_data.get("category_name"),
            menu_category_id=self._safe_int(product_data.get("menu_category_id")),
            unit=product_data.get("unit"),
            cost=self._safe_decimal(product_data.get("cost")),
            cost_netto=self._safe_decimal(product_data.get("cost_netto")),
            weight_flag=bool(product_data.get("weight_flag", False)),
            type=self._safe_int(product_data.get("type")),
            color=product_data.get("color"),
            photo=product_data.get("photo"),
            photo_origin=product_data.get("photo_origin"),
            sort_order=self._safe_int(product_data.get("sort_order")),
            tax_id=self._safe_int(product_data.get("tax_id")),
            product_tax_id=self._safe_int(product_data.get("product_tax_id")),
            fiscal=bool(product_data.get("fiscal", False)),
            fiscal_code=product_data.get("fiscal_code"),
            workshop=self._safe_int(product_data.get("workshop")),
            nodiscount=bool(product_data.get("nodiscount", False)),
            ingredient_id=self._safe_int(product_data.get("ingredient_id")),
            cooking_time=self._safe_int(product_data.get("cooking_time")),
            out=self._safe_int(product_data.get("out")),
            spots=product_data.get("spots"),
            sources=product_data.get("sources"),
            modifications=product_data.get("modifications"),
            ingredients=product_data.get("ingredients"),
            raw_data=product_data,
        )

    def get_product_statistics(self) -> Dict[str, Any]:
        """Get product statistics from database"""
        with self.SessionLocal() as db:
            total_products = db.query(func.count(Product.poster_product_id)).scalar()

            # Get products by category
            category_stats = (
                db.query(
                    Product.category_name,
                    func.count(Product.poster_product_id).label("count"),
                )
                .group_by(Product.category_name)
                .order_by(func.count(Product.poster_product_id).desc())
                .all()
            )

            # Get latest update
            latest_update = db.query(func.max(Product.updated_at)).scalar()

            return {
                "total_products": total_products,
                "categories": [
                    {"name": cat.category_name, "count": cat.count}
                    for cat in category_stats
                ],
                "latest_update": latest_update,
            }

    def _safe_decimal(self, value) -> float:
        """Safely convert value to decimal"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
