from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.logging.providers import get_global_logger
from src.core.models.logging.loguru_service import OptimizedLoguruService
from src.core.database.connection import get_db
from src.core.security.jwt import require_auth, get_current_admin_user, get_current_user
from src.core.loader_factory.api_factory.routes import create_api_router
from src.core.loader_factory.api_factory.controller import create_controller
from .model import Role
from .schemas import (
    RoleCreate,
    RoleUpdate,
    RoleRead,
    RoleWithUsers,
    PermissionAssignment,
    UserRoleAssignment,
)
from .controller import role_controller

# Отримуємо логер з гарантованим fallback на випадок, якщо глобальний логер не ініціалізовано
logger = get_global_logger()
if logger is None:
    # Створюємо локальний екземпляр логера, якщо глобальний недоступний
    logger = OptimizedLoguruService(db_service=None)

# Створюємо стандартний CRUD-роутер за допомогою create_api_router
standard_router = create_api_router(
    controller=create_controller(Role, RoleRead),
    create_schema=RoleCreate,
    update_schema=RoleUpdate,
    response_schema=RoleRead,
    prefix="",
    tags=["roles"],
    auth_dependency=get_current_admin_user,
    admin_dependency=get_current_admin_user,
)

# Створюємо роутери для додаткових специфічних ендпоінтів
protected_router = APIRouter(tags=["roles"], dependencies=[Depends(require_auth)])
admin_router = APIRouter(tags=["roles"], dependencies=[Depends(get_current_admin_user)])

# Об'єднуємо всі роутери в один для експорту
router = APIRouter(tags=["roles"])


# Функція-заміна для insert_log
async def log_action(log_type, log_detail_type, current_user=None):
    """Заміна функції insert_log для логування дій користувача"""
    by_user_id = current_user.get("sub", 0) if current_user else 0
    logger.info(
        f"User action: {log_detail_type}",
        module="auth.roles",
        data={"log_type": log_type, "by_user_id": by_user_id},
    )


# =========================================================
# ЗАХИЩЕНІ ЕНДПОІНТИ (доступні для авторизованих користувачів)
# =========================================================


@protected_router.get("/user/{user_id}", response_model=List[RoleRead])
async def get_user_roles(
    user_id: UUID = Path(..., description="ID користувача"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Отримати всі ролі призначені користувачу.
    Доступно для авторизованих користувачів.
    """
    roles = await role_controller.get_user_roles(db, user_id)

    # Логуємо дію
    await log_action(
        log_type="UserLog",
        log_detail_type="RoleGetUserRoles",
        current_user=current_user,
    )

    return roles


# =========================================================
# СПЕЦІАЛІЗОВАНІ АДМІНІСТРАТИВНІ ЕНДПОІНТИ
# =========================================================

# Видаляємо дублюючі ендпоінти CRUD, які вже є у standard_router


@admin_router.delete("/", response_model=dict)
async def delete_multiple_roles(
    role_ids: List[UUID] = Query(..., description="Список ID ролей для видалення"),
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Видалити декілька ролей за один запит.
    Доступно тільки для адміністраторів.
    """
    deleted_ids = []
    failed_ids = []

    for role_id in role_ids:
        success = await role_controller.remove(db, id=role_id)
        if success:
            deleted_ids.append(str(role_id))
        else:
            failed_ids.append(str(role_id))

    # Логуємо дію
    await log_action(
        log_type="AdminLog",
        log_detail_type="RoleBatchDeleteMany",
        current_user=current_user,
    )

    return {
        "success": len(failed_ids) == 0,
        "message": f"Видалено {len(deleted_ids)} ролей, не знайдено {len(failed_ids)} ролей",
        "deleted_ids": deleted_ids,
        "failed_ids": failed_ids,
    }


@admin_router.put("/{role_id}/permissions", response_model=RoleRead)
async def update_role_permissions(
    permissions: PermissionAssignment,
    role_id: UUID = Path(..., description="ID ролі"),
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Оновити дозволи для існуючої ролі.
    Доступно тільки для адміністраторів.
    """
    # Перевіряємо чи роль існує
    role = await role_controller.get(db, id=role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Роль не знайдено"
        )

    # Оновлюємо дозволи
    updated_role = await role_controller.update_permissions(
        db, role_id, permissions.permissions
    )

    # Логуємо дію
    await log_action(
        log_type="AdminLog",
        log_detail_type="RoleUpdatePermissions",
        current_user=current_user,
    )

    return updated_role


@admin_router.post("/assign-to-user", response_model=dict)
async def assign_role_to_user(
    assignment: UserRoleAssignment,
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Призначити роль користувачу.
    Доступно тільки для адміністраторів.
    """
    success = await role_controller.assign_to_user(
        db, UUID(assignment.user_id), UUID(assignment.role_id)
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Користувача або роль не знайдено",
        )

    # Логуємо дію
    await log_action(
        log_type="AdminLog",
        log_detail_type="RoleAssignToUser",
        current_user=current_user,
    )

    return {"success": success, "message": "Роль успішно призначено користувачу"}


@admin_router.post("/remove-from-user", response_model=dict)
async def remove_role_from_user(
    assignment: UserRoleAssignment,
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Видалити роль у користувача.
    Доступно тільки для адміністраторів.
    """
    success = await role_controller.remove_from_user(
        db, UUID(assignment.user_id), UUID(assignment.role_id)
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Користувача або роль не знайдено",
        )

    # Логуємо дію
    await log_action(
        log_type="AdminLog",
        log_detail_type="RoleRemoveFromUser",
        current_user=current_user,
    )

    return {"success": success, "message": "Роль успішно видалено у користувача"}


# Об'єднання всіх роутерів
router.include_router(standard_router)  # Включаємо стандартний CRUD роутер
router.include_router(protected_router)
router.include_router(admin_router)
