"""
Main Poster service that combines all individual services
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from src.config.settings import settings
from .services import (
    PosterAPIService,
    TransactionService,
    ClientService,
    ProductService,
)

logger = logging.getLogger(__name__)


class PosterService:
    """
    Main Poster service that combines all individual services
    This provides a unified interface for working with Poster API
    """

    def __init__(self):
        # Get credentials from settings
        api_token = settings.POSTER_API_TOKEN
        account_name = settings.POSTER_ACCOUNT_NAME

        if not api_token or not account_name:
            raise ValueError(
                "POSTER_API_TOKEN and POSTER_ACCOUNT_NAME must be configured"
            )

        self.api_service = PosterAPIService(api_token, account_name)
        self.transaction_service = TransactionService(api_token, account_name)
        self.client_service = ClientService(api_token, account_name)
        self.product_service = ProductService(api_token, account_name)

    # API methods delegation
    async def get_transactions(
        self,
        date_from: datetime,
        date_to: datetime,
        page: int = 1,
        per_page: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get transactions from Poster API"""
        return await self.api_service.get_transactions(
            date_from, date_to, page, per_page
        )

    async def get_clients(
        self, offset: int = 0, num: int = 1000, order_by: str = "id", sort: str = "asc"
    ) -> List[Dict[str, Any]]:
        """Get clients from Poster API with pagination support"""
        return await self.api_service.get_clients(offset, num, order_by, sort)


    async def get_products(self) -> List[Dict[str, Any]]:
        """Get products from Poster API"""
        return await self.api_service.get_products()

    # Transaction methods delegation
    def sync_transactions_to_db(
        self, transactions: List[Dict[str, Any]], sync_products: bool = True
    ) -> Dict[str, int]:
        """Sync transactions to database"""
        return self.transaction_service.sync_transactions_to_db(
            transactions, sync_products
        )

    # Client methods delegation
    def sync_clients_to_db(self, clients: List[Dict[str, Any]]) -> Dict[str, int]:
        """Sync clients to database"""
        return self.client_service.sync_clients_to_db(clients)

    def get_last_client_id(self) -> Optional[int]:
        """Get the highest client_id from database for incremental sync"""
        return self.client_service.get_last_client_id()

    # Product methods delegation
    def sync_products_to_db(self, products: List[Dict[str, Any]]) -> Dict[str, int]:
        """Sync products to database"""
        return self.product_service.sync_products_to_db(products)

    def get_product_statistics(self) -> Dict[str, Any]:
        """Get product statistics"""
        return self.product_service.get_product_statistics()

    # Utility methods
    def log_sync_result(
        self, operation: str, status: str, stats: Dict[str, Any]
    ) -> None:
        """Log sync operation result"""
        logger.info(
            f"Sync operation '{operation}' completed with status '{status}': {stats}"
        )

    async def close(self):
        """Close service resources"""
        # If PosterAPIService has no close method, just pass
        pass


# Factory function for backward compatibility
async def get_poster_service() -> PosterService:
    """
    Factory function to get a configured Poster service instance

    Returns:
        PosterService: Configured service instance
    """
    return PosterService()
