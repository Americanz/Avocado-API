"""
Poster API service for making HTTP requests
"""

import logging
from datetime import datetime
from typing import List, Dict, Any
import aiohttp
from .base_service import PosterBaseService

logger = logging.getLogger(__name__)


class PosterAPIService(PosterBaseService):
    """Service for making API calls to Poster"""

    async def get_transactions(
        self,
        date_from: datetime,
        date_to: datetime,
        page: int = 1,
        per_page: int = 1000,
    ) -> List[Dict[str, Any]]:
        """
        Get transactions from Poster API with pagination

        Args:
            date_from: Start date for filtering
            date_to: End date for filtering
            page: Page number (1-based)
            per_page: Number of transactions per page (max 1000)

        Returns:
            List of transaction dictionaries
        """
        params = {
            "token": self.api_token,
            "date_from": date_from.strftime("%Y-%m-%d"),
            "date_to": date_to.strftime("%Y-%m-%d"),
            "page": page,
            "per_page": per_page,
        }

        url = f"{self.base_url}/transactions.getTransactions"

        async with aiohttp.ClientSession() as session:
            try:
                logger.info(
                    f"Fetching transactions from {date_from.strftime('%Y-%m-%d')} to {date_to.strftime('%Y-%m-%d')}"
                )

                async with session.get(url, params=params) as response:
                    response_text = await response.text()

                    if response.status == 200:
                        try:
                            data = await response.json()

                            # Poster API може повертати помилки у відповіді
                            if isinstance(data, dict) and "error" in data:
                                logger.error(f"Poster API error: {data.get('error')}")
                                return []

                            if "response" in data:
                                response_data = data["response"]
                                transactions = response_data.get("data", [])

                                # Діагностика: перевіряємо дати в отриманих транзакціях
                                if transactions:
                                    first_transaction_date = transactions[0].get(
                                        "date_close", "unknown"
                                    )
                                    last_transaction_date = transactions[-1].get(
                                        "date_close", "unknown"
                                    )
                                    logger.info(
                                        f"Received {len(transactions)} transactions (page {page})"
                                    )
                                    logger.info(
                                        f"Date range in response: {first_transaction_date} to {last_transaction_date}"
                                    )
                                    logger.info(
                                        f"Total transactions available: {response_data.get('count', 'unknown')}"
                                    )
                                    page_info = response_data.get("page", {})
                                    logger.info(
                                        f"Page info: {page_info.get('page', 'unknown')}/{page_info.get('per_page', 'unknown')} (count: {page_info.get('count', 'unknown')})"
                                    )
                                else:
                                    logger.info("No transactions returned from API")

                                return transactions
                            else:
                                logger.error(
                                    "Unexpected API response format: missing 'response' field"
                                )
                                return []
                        except Exception as json_error:
                            logger.error(f"Error parsing JSON response: {json_error}")
                            return []
                    else:
                        logger.error(f"API error: {response.status}")
                        error_text = await response.text()
                        logger.error(f"API error details: {error_text}")
                        return []
            except Exception as e:
                logger.error(f"Error fetching transactions: {e}")
                return []

    async def get_products(self) -> List[Dict[str, Any]]:
        """
        Get all products from Poster API
        """
        params = {
            "token": self.api_token,
        }

        url = f"{self.base_url}/menu.getProducts"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "response" in data:
                            if isinstance(data["response"], list):
                                products = data["response"]
                                logger.info(f"Received {len(products)} products")
                                return products
                            elif (
                                isinstance(data["response"], dict)
                                and "data" in data["response"]
                            ):
                                products = data["response"]["data"]
                                logger.info(f"Received {len(products)} products")
                                return products
                            else:
                                logger.error(
                                    "Unexpected API response format for products"
                                )
                                return []
                        else:
                            logger.error("No 'response' key in API response")
                            return []
                    else:
                        logger.error(f"API error: {response.status}")
                        return []
            except Exception as e:
                logger.error(f"Error fetching products: {e}")
                return []

    async def get_clients(
        self, offset: int = 0, num: int = 1000, order_by: str = "id", sort: str = "asc"
    ) -> List[Dict[str, Any]]:
        """
        Get clients from Poster API with pagination support for incremental sync

        Args:
            offset: Starting offset (number of records to skip)
            num: Number of records to fetch (max 1000)
            order_by: Field to order by (default: "id")
            sort: Sort direction "asc" or "desc" (default: "asc")
        """
        params = {
            "token": self.api_token,
            "offset": offset,
            "num": num,
            "order_by": order_by,
            "sort": sort,
        }

        url = f"{self.base_url}/clients.getClients"

        async with aiohttp.ClientSession() as session:
            try:
                logger.info(f"Fetching clients with offset={offset}, num={num}")
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(
                            f"Clients API response structure: {list(data.keys())}"
                        )
                        if "response" in data:
                            response_data = data["response"]
                            logger.info(
                                f"Response data keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}"
                            )
                            if isinstance(response_data, list):
                                clients = response_data
                                logger.info(
                                    f"Received {len(clients)} clients (direct list)"
                                )
                                return clients
                            elif (
                                isinstance(response_data, dict)
                                and "data" in response_data
                            ):
                                clients = response_data["data"]
                                logger.info(
                                    f"Received {len(clients)} clients (nested data)"
                                )
                                return clients
                            else:
                                logger.warning(
                                    f"Unexpected response format: {response_data}"
                                )
                                return []
                        else:
                            logger.error("No 'response' key in API response")
                            return []
                    else:
                        logger.error(f"API error: {response.status}")
                        return []
            except Exception as e:
                logger.error(f"Error fetching clients: {e}")
                return []

    async def get_spots(self) -> List[Dict[str, Any]]:
        """
        Get all spots (locations) from Poster API

        Returns:
            List of spot dictionaries with fields: spot_id, name, address
        """
        params = {
            "token": self.api_token,
        }

        url = f"{self.base_url}/spots.getSpots"

        async with aiohttp.ClientSession() as session:
            try:
                logger.info("Fetching spots from Poster API")
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(
                            f"Spots API response structure: {list(data.keys())}"
                        )
                        if "response" in data:
                            response_data = data["response"]
                            logger.info(
                                f"Response data keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}"
                            )
                            if isinstance(response_data, list):
                                spots = response_data
                                logger.info(
                                    f"Received {len(spots)} spots (direct list)"
                                )
                                return spots
                            elif (
                                isinstance(response_data, dict)
                                and "data" in response_data
                            ):
                                spots = response_data["data"]
                                logger.info(
                                    f"Received {len(spots)} spots (nested data)"
                                )
                                return spots
                            else:
                                logger.warning(
                                    f"Unexpected response format: {response_data}"
                                )
                                return []
                        else:
                            logger.error("No 'response' key in API response")
                            return []
                    else:
                        logger.error(f"API error: {response.status}")
                        error_text = await response.text()
                        logger.error(f"API error details: {error_text}")
                        return []
            except Exception as e:
                logger.error(f"Error fetching spots: {e}")
                return []
