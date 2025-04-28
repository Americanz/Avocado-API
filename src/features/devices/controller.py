"""
Controller for device management.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.devices.model import Device, DeviceStatus, DeviceType
from src.features.devices.schemas import DeviceCreate, DeviceUpdate


class DeviceController:
    """Controller for handling device-related business logic."""

    def __init__(self, db: AsyncSession):
        """
        Initialize device controller with database session.

        Args:
            db: Database session
        """
        self.db = db

    async def get_by_id(self, device_id: UUID) -> Optional[Device]:
        """
        Get device by ID.

        Args:
            device_id: Device ID

        Returns:
            Device object or None if not found
        """
        result = await self.db.execute(select(Device).where(Device.id == device_id))
        return result.scalar_one_or_none()

    async def get_by_device_id(self, device_unique_id: str) -> Optional[Device]:
        """
        Get device by unique device_id.

        Args:
            device_unique_id: Unique device identifier

        Returns:
            Device object or None if not found
        """
        result = await self.db.execute(select(Device).where(Device.device_id == device_unique_id))
        return result.scalar_one_or_none()

    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        filter_params: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, List[Device]]:
        """
        Get all devices with filtering and pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filter_params: Optional filter parameters

        Returns:
            Tuple of (total count, list of devices)
        """
        # Base query
        query = select(Device)
        
        # Apply filters if provided
        if filter_params:
            if filter_params.get("name"):
                query = query.where(Device.name.ilike(f"%{filter_params['name']}%"))
            if filter_params.get("device_type"):
                query = query.where(Device.device_type == filter_params["device_type"])
            if filter_params.get("status"):
                query = query.where(Device.status == filter_params["status"])
            if filter_params.get("platform"):
                query = query.where(Device.platform.ilike(f"%{filter_params['platform']}%"))
            if filter_params.get("user_id"):
                query = query.where(Device.user_id == filter_params["user_id"])
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0
        
        # Apply pagination
        query = query.offset(skip).limit(limit).order_by(Device.created_at.desc())
        
        # Execute query
        result = await self.db.execute(query)
        devices = result.scalars().all()
        
        return total_count, list(devices)

    async def create(self, device_data: DeviceCreate) -> Device:
        """
        Create a new device.

        Args:
            device_data: Device data for creation

        Returns:
            Created Device object
        """
        # Create new device
        device = Device(**device_data.model_dump())
        
        # Add device to database
        self.db.add(device)
        await self.db.commit()
        await self.db.refresh(device)
        
        return device

    async def update(self, device_id: UUID, device_data: DeviceUpdate) -> Optional[Device]:
        """
        Update a device.

        Args:
            device_id: Device ID
            device_data: Device data for update

        Returns:
            Updated Device object or None if not found
        """
        # Get device
        device = await self.get_by_id(device_id)
        if not device:
            return None
        
        # Update device fields
        update_data = device_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(device, field, value)
        
        # Save changes
        await self.db.commit()
        await self.db.refresh(device)
        
        return device

    async def update_last_active(self, device_id: UUID) -> bool:
        """
        Update device's last active timestamp.

        Args:
            device_id: Device ID

        Returns:
            True if updated, False if device not found
        """
        result = await self.db.execute(
            update(Device)
            .where(Device.id == device_id)
            .values(last_active=datetime.utcnow())
            .returning(Device.id)
        )
        updated = result.scalar_one_or_none()
        
        if updated:
            await self.db.commit()
            return True
        
        return False

    async def delete(self, device_id: UUID) -> bool:
        """
        Delete a device.

        Args:
            device_id: Device ID

        Returns:
            True if deleted, False if not found
        """
        # Get device
        device = await self.get_by_id(device_id)
        if not device:
            return False
        
        # Delete device
        await self.db.delete(device)
        await self.db.commit()
        
        return True

    async def update_status(self, device_id: UUID, status: DeviceStatus) -> Optional[Device]:
        """
        Update device status.

        Args:
            device_id: Device ID
            status: New device status

        Returns:
            Updated Device object or None if not found
        """
        # Get device
        device = await self.get_by_id(device_id)
        if not device:
            return None
        
        # Update status
        device.status = status
        
        # Save changes
        await self.db.commit()
        await self.db.refresh(device)
        
        return device

    async def update_push_token(self, device_id: UUID, push_token: str) -> Optional[Device]:
        """
        Update device push token.

        Args:
            device_id: Device ID
            push_token: New push token

        Returns:
            Updated Device object or None if not found
        """
        # Get device
        device = await self.get_by_id(device_id)
        if not device:
            return None
        
        # Update push token
        device.push_token = push_token
        
        # Save changes
        await self.db.commit()
        await self.db.refresh(device)
        
        return device
