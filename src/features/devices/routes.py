"""
API routes for device management.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.connection import get_db
from src.core.models.logging.providers import get_global_logger
from src.core.models.logging.loguru_service import OptimizedLoguruService
from src.core.security.jwt import require_auth, get_current_admin_user, get_current_user

from src.features.devices.controller import DeviceController
from src.features.devices.model import DeviceStatus, DeviceType
from src.features.devices.schemas import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    DevicePaginationResponse,
    DeviceFilter,
)

# Отримуємо логер з гарантованим fallback на випадок, якщо глобальний логер не ініціалізовано
logger = get_global_logger()
if logger is None:
    # Створюємо локальний екземпляр логера, якщо глобальний недоступний
    logger = OptimizedLoguruService(db_service=None)

# Створюємо роутери для різних рівнів доступу
protected_router = APIRouter(tags=["devices"], dependencies=[Depends(require_auth)])
admin_router = APIRouter(tags=["devices"], dependencies=[Depends(get_current_admin_user)])

# Об'єднуємо всі роутери в один для експорту
router = APIRouter(tags=["devices"])

# Функція для створення контролера пристроїв
def get_device_controller(db: AsyncSession = Depends(get_db)) -> DeviceController:
    """Dependency for getting DeviceController instance."""
    return DeviceController(db)

# Функція для логування дій
async def log_action(action_type: str, detail: str, current_user=None):
    """Log user action."""
    by_user_id = current_user.get("sub", "0") if current_user else "0"
    logger.info(
        f"Device action: {detail}",
        module="features.devices",
        data={"action_type": action_type, "by_user_id": by_user_id},
    )

# =========================================================
# ЗАХИЩЕНІ ЕНДПОІНТИ (доступні для авторизованих користувачів)
# =========================================================

@protected_router.get("/", response_model=DevicePaginationResponse)
async def list_devices(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    name: Optional[str] = Query(None, description="Filter by device name"),
    device_type: Optional[DeviceType] = Query(None, description="Filter by device type"),
    status: Optional[DeviceStatus] = Query(None, description="Filter by device status"),
    platform: Optional[str] = Query(None, description="Filter by device platform"),
    current_user: dict = Depends(get_current_user),
    controller: DeviceController = Depends(get_device_controller),
):
    """
    Get list of all devices with filtering and pagination.
    """
    filter_params = {}
    if name:
        filter_params["name"] = name
    if device_type:
        filter_params["device_type"] = device_type
    if status:
        filter_params["status"] = status
    if platform:
        filter_params["platform"] = platform

    # Get devices
    total, devices = await controller.get_all(
        skip=skip,
        limit=limit,
        filter_params=filter_params
    )

    # Log action
    await log_action(
        action_type="READ",
        detail=f"List devices (skip={skip}, limit={limit})",
        current_user=current_user,
    )

    return {
        "total": total,
        "items": devices
    }


@protected_router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: UUID = Path(..., description="The ID of the device to get"),
    current_user: dict = Depends(get_current_user),
    controller: DeviceController = Depends(get_device_controller),
):
    """
    Get a specific device by ID.
    """
    device = await controller.get_by_id(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
        )

    # Update last active timestamp
    await controller.update_last_active(device_id)

    # Log action
    await log_action(
        action_type="READ",
        detail=f"Get device: {device_id}",
        current_user=current_user,
    )

    return device


@protected_router.get("/by-device-id/{device_unique_id}", response_model=DeviceResponse)
async def get_device_by_unique_id(
    device_unique_id: str = Path(..., description="The unique device ID"),
    current_user: dict = Depends(get_current_user),
    controller: DeviceController = Depends(get_device_controller),
):
    """
    Get a specific device by its unique device_id.
    """
    device = await controller.get_by_device_id(device_unique_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
        )

    # Update last active timestamp
    await controller.update_last_active(device.id)

    # Log action
    await log_action(
        action_type="READ",
        detail=f"Get device by unique ID: {device_unique_id}",
        current_user=current_user,
    )

    return device


@protected_router.post(
    "/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED
)
async def create_device(
    device_data: DeviceCreate,
    current_user: dict = Depends(get_current_user),
    controller: DeviceController = Depends(get_device_controller),
):
    """
    Create a new device.
    """
    # Check if device with given ID already exists
    existing_device = await controller.get_by_device_id(device_data.device_id)
    if existing_device:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Device with ID '{device_data.device_id}' already exists"
        )

    # Create device
    device = await controller.create(device_data)

    # Log action
    await log_action(
        action_type="CREATE",
        detail=f"Create device: {device.name} ({device.device_id})",
        current_user=current_user,
    )

    return device


@protected_router.patch("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_data: DeviceUpdate,
    device_id: UUID = Path(..., description="The ID of the device to update"),
    current_user: dict = Depends(get_current_user),
    controller: DeviceController = Depends(get_device_controller),
):
    """
    Update a device.
    """
    # Check if device exists
    device = await controller.get_by_id(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
        )

    # Update device
    updated_device = await controller.update(device_id, device_data)

    # Log action
    await log_action(
        action_type="UPDATE",
        detail=f"Update device: {device_id}",
        current_user=current_user,
    )

    return updated_device


@protected_router.patch("/{device_id}/status", response_model=DeviceResponse)
async def update_device_status(
    status: DeviceStatus,
    device_id: UUID = Path(..., description="The ID of the device to update"),
    current_user: dict = Depends(get_current_user),
    controller: DeviceController = Depends(get_device_controller),
):
    """
    Update device status.
    """
    # Check if device exists
    device = await controller.get_by_id(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
        )

    # Update status
    updated_device = await controller.update_status(device_id, status)

    # Log action
    await log_action(
        action_type="UPDATE",
        detail=f"Update device status: {device_id} -> {status}",
        current_user=current_user,
    )

    return updated_device


@protected_router.patch("/{device_id}/push-token", response_model=DeviceResponse)
async def update_device_push_token(
    push_token: str,
    device_id: UUID = Path(..., description="The ID of the device to update"),
    current_user: dict = Depends(get_current_user),
    controller: DeviceController = Depends(get_device_controller),
):
    """
    Update device push token.
    """
    # Check if device exists
    device = await controller.get_by_id(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
        )

    # Update push token
    updated_device = await controller.update_push_token(device_id, push_token)

    # Log action
    await log_action(
        action_type="UPDATE",
        detail=f"Update device push token: {device_id}",
        current_user=current_user,
    )

    return updated_device


# =========================================================
# АДМІНІСТРАТИВНІ ЕНДПОІНТИ (доступні тільки для адміністраторів)
# =========================================================

@admin_router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: UUID = Path(..., description="The ID of the device to delete"),
    current_user: dict = Depends(get_current_admin_user),
    controller: DeviceController = Depends(get_device_controller),
):
    """
    Delete a device.
    Admin access required.
    """
    # Check if device exists and delete it
    success = await controller.delete(device_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
        )

    # Log action
    await log_action(
        action_type="DELETE",
        detail=f"Delete device: {device_id}",
        current_user=current_user,
    )

    return None

# Об'єднання всіх роутерів
router.include_router(protected_router)
router.include_router(admin_router)
