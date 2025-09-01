"""
Service for managing Poster spots (locations)
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from ...models.spot import Spot
from ...schemas.spot import SpotCreate, SpotUpdate
from .api_service import PosterAPIService

logger = logging.getLogger(__name__)


class PosterSpotService:
    """Service for managing Poster spots data"""

    def __init__(self, db: Session, api_service: PosterAPIService):
        self.db = db
        self.api_service = api_service

    async def sync_spots(self) -> Dict[str, Any]:
        """
        Synchronize spots from Poster API to database

        Returns:
            Dictionary with sync statistics
        """
        try:
            logger.info("Starting spots synchronization")

            # Fetch spots from API
            api_spots = await self.api_service.get_spots()
            if not api_spots:
                logger.warning("No spots received from API")
                return {
                    "status": "no_data",
                    "message": "No spots received from API",
                    "spots_processed": 0,
                    "spots_created": 0,
                    "spots_updated": 0,
                }

            spots_processed = 0
            spots_created = 0
            spots_updated = 0

            for spot_data in api_spots:
                try:
                    spot_id = spot_data.get("spot_id")
                    if not spot_id:
                        logger.warning(f"Spot without ID: {spot_data}")
                        continue

                    # Check if spot exists
                    existing_spot = self.db.execute(
                        select(Spot).where(Spot.spot_id == spot_id)
                    ).scalar_one_or_none()

                    if existing_spot:
                        # Update existing spot
                        update_data = SpotUpdate(
                            name=spot_data.get("name"), address=spot_data.get("address")
                        )
                        self._update_spot(existing_spot, update_data)
                        spots_updated += 1
                        logger.debug(f"Updated spot {spot_id}")
                    else:
                        # Create new spot
                        create_data = SpotCreate(
                            spot_id=spot_id,
                            name=spot_data.get("name"),
                            address=spot_data.get("address"),
                        )
                        self._create_spot(create_data)
                        spots_created += 1
                        logger.debug(f"Created spot {spot_id}")

                    spots_processed += 1

                except Exception as e:
                    logger.error(
                        f"Error processing spot {spot_data.get('spot_id', 'unknown')}: {e}"
                    )
                    continue

            # Commit all changes
            self.db.commit()

            logger.info(
                f"Spots sync completed: {spots_processed} processed, {spots_created} created, {spots_updated} updated"
            )

            return {
                "status": "success",
                "message": "Spots synchronized successfully",
                "spots_processed": spots_processed,
                "spots_created": spots_created,
                "spots_updated": spots_updated,
            }

        except Exception as e:
            logger.error(f"Error during spots synchronization: {e}")
            self.db.rollback()
            return {
                "status": "error",
                "message": f"Error during spots synchronization: {str(e)}",
                "spots_processed": 0,
                "spots_created": 0,
                "spots_updated": 0,
            }

    def _create_spot(self, spot_data: SpotCreate) -> Spot:
        """Create a new spot"""
        db_spot = Spot(
            spot_id=spot_data.spot_id, name=spot_data.name, address=spot_data.address
        )
        self.db.add(db_spot)
        return db_spot

    def _update_spot(self, db_spot: Spot, spot_data: SpotUpdate) -> Spot:
        """Update an existing spot"""
        if spot_data.name is not None:
            db_spot.name = spot_data.name
        if spot_data.address is not None:
            db_spot.address = spot_data.address
        return db_spot

    def get_spot_by_id(self, spot_id: str) -> Optional[Spot]:
        """Get spot by ID"""
        return self.db.execute(
            select(Spot).where(Spot.spot_id == spot_id)
        ).scalar_one_or_none()

    def get_all_spots(self) -> List[Spot]:
        """Get all spots"""
        return self.db.execute(select(Spot)).scalars().all()

    def get_spots_count(self) -> int:
        """Get total number of spots"""
        return self.db.execute(select(Spot)).scalar()
