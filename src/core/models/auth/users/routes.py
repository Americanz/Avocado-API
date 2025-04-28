"""
Маршрути API для керування користувачами.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Query,
    Path,
    Form,
    status,
    Request,  # Додано імпорт Request
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.connection import get_db
from src.core.models.logging.providers import get_global_logger
from src.core.security.jwt import get_current_user, require_auth, get_current_admin_user
from src.core.models.auth.users.controller import UserController
from src.core.models.auth.users.schemas import (
    UserCreate,
    UserUpdate,
)

from src.core.schemas.responses import Success, Fail, SuccessExtra
from src.config.settings import settings

# Отримуємо логер
logger = get_global_logger()

# Створюємо роутер
router = APIRouter(tags=["users"])


# Функція для отримання контролера
def get_controller(db: AsyncSession = Depends(get_db)):
    return UserController(db=db)


# Функція для логування дій
async def log_action(action_type: str, detail: str, user_id: Optional[str] = None):
    """Логування дій користувача."""
    if logger:
        logger.info(
            f"User action: {detail}",
            module="auth.users",
            data={"action_type": action_type, "user_id": user_id},
        )


# ==============================================
# ПУБЛІЧНІ ЕНДПОІНТИ (доступні без авторизації)
# ==============================================


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    controller=Depends(get_controller),
):
    """Реєстрація нового користувача."""
    try:
        user = await controller.create(user_data)

        # Логуємо дію
        await log_action(
            action_type="CREATE",
            detail=f"User registered: {user.email}",
            user_id=str(user.id),
        )

        user_data = controller.prepare_user_response(user)
        return Success(data=user_data, msg="Користувач успішно зареєстрований")
    except Exception as e:
        return Fail(
            code="4000",
            msg=f"Помилка при створенні користувача: {str(e)}",
        )


@router.post("/login")
async def login_user(
    request: Request,  # Додано об'єкт Request
    username: str = Form(...),
    password: str = Form(...),
    controller=Depends(get_controller),
):
    """Вхід користувача за допомогою форми."""
    if not settings.ENABLE_PASSWORD_AUTH:
        return Fail(
            code="4004",
            msg="Автентифікація за паролем вимкнена",
        )

    user = await controller.authenticate(username, password)
    if not user:
        return Fail(
            code="4001",
            msg="Невірний логін або пароль",
        )

    # Логуємо дію
    await log_action(
        action_type="AUTH",
        detail=f"User login (form): {user.email}",
        user_id=str(user.id),
    )

    token_data = controller.create_access_token_for_user(user)

    # Визначаємо, чи запит надійшов з Swagger UI
    is_swagger_request = False
    user_agent = request.headers.get("user-agent", "")
    referer = request.headers.get("referer", "")

    # Swagger UI використовує специфічний User-Agent або викликається з /docs
    if "swagger" in user_agent.lower() or "/docs" in referer:
        is_swagger_request = True

    # Для OAuth2 в документації повертаємо стандартний формат без обгортки Success
    if is_swagger_request:
        return token_data.model_dump()

    # Для API-клієнтів повертаємо в нашому стандартному форматі
    return Success(data=token_data.model_dump(), msg="Успішний вхід")


# =========================================================
# ЗАХИЩЕНІ ЕНДПОІНТИ (доступні тільки авторизованим користувачам)
# =========================================================


@router.get("/me", dependencies=[Depends(require_auth)])
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    controller=Depends(get_controller),
):
    """Отримати профіль поточного користувача."""
    user = await controller.get_by_id(current_user["sub"])
    if not user:
        return Fail(
            code="4004",
            msg="Користувача не знайдено",
        )

    # Логуємо дію
    await log_action(
        action_type="READ",
        detail=f"Get current user profile: {user.email}",
        user_id=str(user.id),
    )

    user_data = controller.prepare_user_response(user)
    return Success(data=user_data)


@router.patch("/me", dependencies=[Depends(require_auth)])
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    controller=Depends(get_controller),
):
    """Оновити профіль поточного користувача."""
    user = await controller.update(current_user["sub"], user_data)
    if not user:
        return Fail(
            code="4004",
            msg="Користувача не знайдено",
        )

    # Логуємо дію
    await log_action(
        action_type="UPDATE",
        detail=f"Update current user profile: {user.email}",
        user_id=str(user.id),
    )

    user_data = controller.prepare_user_response(user)
    return Success(data=user_data, msg="Профіль успішно оновлено")


@router.get("/{user_id}/has-role/{role_name}", dependencies=[Depends(require_auth)])
async def check_user_has_role(
    user_id: UUID = Path(..., description="ID користувача"),
    role_name: str = Path(..., description="Назва ролі"),
    current_user: dict = Depends(get_current_user),
    controller=Depends(get_controller),
):
    """Перевірити, чи користувач має певну роль."""
    has_role = await controller.has_role(user_id, role_name)

    # Логуємо дію
    await log_action(
        action_type="READ",
        detail=f"Check if user {user_id} has role '{role_name}'",
        user_id=current_user.get("sub"),
    )

    return Success(
        data={
            "has_role": has_role,
            "user_id": str(user_id),
            "role_name": role_name,
        }
    )


@router.get(
    "/{user_id}/has-permission/{permission_name}", dependencies=[Depends(require_auth)]
)
async def check_user_has_permission(
    user_id: UUID = Path(..., description="ID користувача"),
    permission_name: str = Path(..., description="Назва дозволу"),
    current_user: dict = Depends(get_current_user),
    controller=Depends(get_controller),
):
    """Перевірити, чи користувач має певний дозвіл."""
    has_permission = await controller.has_permission(user_id, permission_name)

    # Логуємо дію
    await log_action(
        action_type="READ",
        detail=f"Check if user {user_id} has permission '{permission_name}'",
        user_id=current_user.get("sub"),
    )

    return Success(
        data={
            "has_permission": has_permission,
            "user_id": str(user_id),
            "permission_name": permission_name,
        }
    )


# =========================================================
# АДМІНІСТРАТИВНІ ЕНДПОІНТИ (доступні тільки для адміністраторів)
# =========================================================


@router.get("/", dependencies=[Depends(get_current_admin_user)])
async def list_users(
    skip: int = Query(0, ge=0, description="Кількість записів для пропуску"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальна кількість записів"),
    search: Optional[str] = Query(None, description="Пошуковий запит"),
    current_user: dict = Depends(get_current_user),
    controller=Depends(get_controller),
):
    """Отримати список користувачів з пагінацією та пошуком."""
    # Обчислюємо сторінку
    page = (skip // limit) + 1

    # Отримуємо список користувачів
    total, users = await controller.list(
        page=page,
        page_size=limit,
        search_term=search,
    )

    # Готуємо відповідь
    user_responses = [controller.prepare_user_response(user) for user in users]

    # Логуємо дію
    await log_action(
        action_type="READ",
        detail=f"List users (skip={skip}, limit={limit})",
        user_id=current_user.get("sub"),
    )

    return SuccessExtra(
        data=user_responses,
        total=total,
        current=page,
        size=limit,
    )


@router.get("/{user_id}", dependencies=[Depends(get_current_admin_user)])
async def get_user(
    user_id: UUID = Path(..., description="ID користувача"),
    current_user: dict = Depends(get_current_user),
    controller=Depends(get_controller),
):
    """Отримати інформацію про користувача за ID."""
    user = await controller.get_by_id(str(user_id))
    if not user:
        return Fail(
            code="4004",
            msg="Користувача не знайдено",
        )

    # Логуємо дію
    await log_action(
        action_type="READ",
        detail=f"Get user: {user.email}",
        user_id=current_user.get("sub"),
    )

    user_data = controller.prepare_user_response(user)
    return Success(data=user_data)


@router.delete("/{user_id}", dependencies=[Depends(get_current_admin_user)])
async def delete_user(
    user_id: UUID = Path(..., description="ID користувача"),
    current_user: dict = Depends(get_current_user),
    controller=Depends(get_controller),
):
    """Видалити користувача за ID."""
    success = await controller.delete(str(user_id))
    if not success:
        return Fail(
            code="4004",
            msg="Користувача не знайдено",
        )

    # Логуємо дію
    await log_action(
        action_type="DELETE",
        detail=f"Delete user: {user_id}",
        user_id=current_user.get("sub"),
    )

    return Success(msg="Користувача успішно видалено")


@router.get("/{user_id}/roles", dependencies=[Depends(get_current_admin_user)])
async def get_user_roles(
    user_id: UUID = Path(..., description="ID користувача"),
    current_user: dict = Depends(get_current_user),
    controller=Depends(get_controller),
):
    """Отримати всі ролі, призначені користувачу."""
    roles = await controller.get_user_roles(user_id)

    # Перетворюємо ролі у формат відповіді
    role_responses = [
        {
            "id": str(role.id),
            "name": role.name,
            "description": role.description,
        }
        for role in roles
    ]

    # Логуємо дію
    await log_action(
        action_type="READ",
        detail=f"Get user roles: {user_id}",
        user_id=current_user.get("sub"),
    )

    return Success(data=role_responses)


@router.post(
    "/{user_id}/roles/{role_id}", dependencies=[Depends(get_current_admin_user)]
)
async def assign_role_to_user(
    user_id: UUID = Path(..., description="ID користувача"),
    role_id: UUID = Path(..., description="ID ролі"),
    current_user: dict = Depends(get_current_user),
    controller=Depends(get_controller),
):
    """Призначити роль користувачу."""
    success = await controller.assign_role(user_id, role_id)
    if not success:
        return Fail(
            code="4004",
            msg="Користувача або роль не знайдено",
        )

    # Логуємо дію
    await log_action(
        action_type="UPDATE",
        detail=f"Assign role {role_id} to user {user_id}",
        user_id=current_user.get("sub"),
    )

    return Success(
        data={
            "success": True,
            "user_id": str(user_id),
            "role_id": str(role_id),
        },
        msg="Роль успішно призначено користувачу",
    )


@router.delete(
    "/{user_id}/roles/{role_id}", dependencies=[Depends(get_current_admin_user)]
)
async def remove_role_from_user(
    user_id: UUID = Path(..., description="ID користувача"),
    role_id: UUID = Path(..., description="ID ролі"),
    current_user: dict = Depends(get_current_user),
    controller=Depends(get_controller),
):
    """Видалити роль у користувача."""
    success = await controller.remove_role(user_id, role_id)
    if not success:
        return Fail(
            code="4004",
            msg="Користувача або роль не знайдено",
        )

    # Логуємо дію
    await log_action(
        action_type="UPDATE",
        detail=f"Remove role {role_id} from user {user_id}",
        user_id=current_user.get("sub"),
    )

    return Success(
        data={
            "success": True,
            "user_id": str(user_id),
            "role_id": str(role_id),
        },
        msg="Роль успішно видалено у користувача",
    )


@router.put("/{user_id}/roles", dependencies=[Depends(get_current_admin_user)])
async def set_user_roles(
    user_id: UUID = Path(..., description="ID користувача"),
    role_ids: List[UUID] = None,
    current_user: dict = Depends(get_current_user),
    controller=Depends(get_controller),
):
    """Встановити ролі користувача (замінити всі існуючі ролі новими)."""
    success = await controller.set_user_roles(user_id, role_ids or [])
    if not success:
        return Fail(
            code="4004",
            msg="Користувача не знайдено",
        )

    # Логуємо дію
    await log_action(
        action_type="UPDATE",
        detail=f"Set roles for user {user_id}",
        user_id=current_user.get("sub"),
    )

    return Success(
        data={
            "success": True,
            "user_id": str(user_id),
            "role_ids": [str(role_id) for role_id in (role_ids or [])],
        },
        msg="Ролі користувача успішно оновлено",
    )
