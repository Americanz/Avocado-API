"""
Poster client synchronization service
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import func
from .base_service import PosterBaseService
from ...models import Client

logger = logging.getLogger(__name__)


class ClientService(PosterBaseService):
    """Service for synchronizing Poster clients"""

    def get_last_client_id(self) -> Optional[int]:
        """
        Get the highest client_id from database to use as offset for incremental sync

        Returns:
            Optional[int]: Highest client_id or None if no clients exist
        """
        with self.SessionLocal() as db:
            try:
                result = db.query(func.max(Client.client_id)).scalar()
                logger.info(f"Last client_id in database: {result}")
                return result
            except Exception as e:
                logger.error(f"Error getting last client_id: {e}")
                return None

    def sync_clients_to_db(self, clients: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Sync clients to database with optimized batch processing

        Args:
            clients: List of client data from API

        Returns:
            Dictionary with sync statistics
        """
        stats = {"processed": 0, "created": 0, "updated": 0, "errors": 0}

        with self.SessionLocal() as db:
            try:
                logger.info(f"Starting batch sync of {len(clients)} clients...")

                # Get existing client IDs for this batch
                client_ids = [int(client_data["client_id"]) for client_data in clients]
                existing_clients = (
                    db.query(Client).filter(Client.client_id.in_(client_ids)).all()
                )
                existing_ids = {c.client_id for c in existing_clients}
                # Create lookup dictionary for fast access
                existing_clients_dict = {c.client_id: c for c in existing_clients}

                logger.info(
                    f"Found {len(existing_ids)} existing clients, {len(clients) - len(existing_ids)} new"
                )

                # Process clients in batch
                new_clients = []
                update_mappings = []

                for client_data in clients:
                    try:
                        stats["processed"] += 1
                        client_id = int(client_data["client_id"])

                        if client_id in existing_ids:
                            # Prepare update data for bulk update
                            existing_client = existing_clients_dict[client_id]
                            update_data = self._prepare_client_update_data(
                                existing_client.id, client_data
                            )
                            update_mappings.append(update_data)
                            stats["updated"] += 1
                        else:
                            # Prepare new client
                            client = self._create_client(client_data)
                            new_clients.append(client)
                            stats["created"] += 1

                    except Exception as e:
                        stats["errors"] += 1
                        logger.error(
                            f"Error processing client {client_data.get('client_id')}: {e}"
                        )
                        continue

                # Bulk operations
                if update_mappings:
                    logger.info(
                        f"Bulk updating {len(update_mappings)} existing clients..."
                    )
                    db.bulk_update_mappings(Client, update_mappings)

                if new_clients:
                    logger.info(f"Bulk inserting {len(new_clients)} new clients...")
                    db.add_all(new_clients)

                # Commit all changes
                db.commit()
                logger.info(f"Batch sync completed: {stats}")

            except Exception as e:
                db.rollback()
                logger.error(f"Database error during batch sync: {e}")
                raise

        return stats

    def _prepare_client_update_data(
        self, client_db_id: str, client_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare client data for bulk update"""
        # Parse birthday
        birthday_str = client_data.get("birthday")
        if birthday_str and birthday_str != "0000-00-00":
            birthday = birthday_str
        else:
            birthday = None

        # Parse date_activale
        date_activale = None
        if client_data.get("date_activale"):
            try:
                date_activale = datetime.strptime(
                    client_data["date_activale"], "%Y-%m-%d %H:%M:%S"
                )
            except ValueError:
                pass

        return {
            "id": client_db_id,  # Primary key for update
            "firstname": client_data.get("firstname"),
            "lastname": client_data.get("lastname"),
            "patronymic": client_data.get("patronymic"),
            "phone": client_data.get("phone"),
            "phone_number": client_data.get("phone_number"),
            "email": client_data.get("email"),
            "birthday": birthday,
            "client_sex": client_data.get("client_sex"),
            "country": client_data.get("country"),
            "city": client_data.get("city"),
            "address": client_data.get("address"),
            "addresses": client_data.get("addresses"),
            "card_number": client_data.get("card_number"),
            "comment": client_data.get("comment"),
            "discount_per": self._safe_decimal(client_data.get("discount_per")),
            "bonus": self._safe_decimal(client_data.get("bonus")),
            "total_payed_sum": self._safe_decimal(client_data.get("total_payed_sum")),
            "client_groups_id": client_data.get("client_groups_id"),
            "client_groups_name": client_data.get("client_groups_name"),
            "client_groups_discount": self._safe_decimal(
                client_data.get("client_groups_discount")
            ),
            "loyalty_type": client_data.get("loyalty_type"),
            "birthday_bonus": self._safe_decimal(client_data.get("birthday_bonus")),
            "date_activale": date_activale,
            "delete": self._safe_bool(client_data.get("delete")),
            "ewallet": self._safe_decimal(client_data.get("ewallet")),
            "raw_data": client_data,
            "last_sync_from_poster": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

    def _create_client(self, client_data: Dict[str, Any]) -> Client:
        """Create Client from API data"""
        # Parse birthday
        birthday_str = client_data.get("birthday")
        if birthday_str and birthday_str != "0000-00-00":
            birthday = birthday_str
        else:
            birthday = None

        # Parse date_activale
        date_activale = None
        if client_data.get("date_activale"):
            try:
                date_activale = datetime.strptime(
                    client_data["date_activale"], "%Y-%m-%d %H:%M:%S"
                )
            except ValueError:
                pass

        return Client(
            client_id=int(client_data["client_id"]),
            firstname=client_data.get("firstname"),
            lastname=client_data.get("lastname"),
            patronymic=client_data.get("patronymic"),
            phone=client_data.get("phone"),
            phone_number=client_data.get("phone_number"),
            email=client_data.get("email"),
            birthday=birthday,
            client_sex=client_data.get("client_sex"),
            country=client_data.get("country"),
            city=client_data.get("city"),
            address=client_data.get("address"),
            addresses=client_data.get("addresses"),
            card_number=client_data.get("card_number"),
            comment=client_data.get("comment"),
            discount_per=self._safe_decimal(client_data.get("discount_per")),
            bonus=self._safe_decimal(client_data.get("bonus")),
            total_payed_sum=self._safe_decimal(client_data.get("total_payed_sum")),
            client_groups_id=client_data.get("client_groups_id"),
            client_groups_name=client_data.get("client_groups_name"),
            client_groups_discount=self._safe_decimal(
                client_data.get("client_groups_discount")
            ),
            loyalty_type=client_data.get("loyalty_type"),
            birthday_bonus=self._safe_decimal(client_data.get("birthday_bonus")),
            date_activale=date_activale,
            delete=self._safe_bool(client_data.get("delete")),
            ewallet=self._safe_decimal(client_data.get("ewallet")),
            raw_data=client_data,
        )
