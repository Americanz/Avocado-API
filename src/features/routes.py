"""
Main API router for the application with generic CRUD support.
"""

from fastapi import APIRouter, Depends

from src.config.constants import API_VERSION_PREFIX
from src.core.security.jwt import require_auth, get_current_admin_user
from src.core.security.router import create_protected_router

# Імпорт існуючих роутерів
from src.core.models.auth.users.routes import router as users_router
from src.core.models.logging.routes import router as logs_router

# Імпорт фабрики для генерації роутерів на основі моделей
from src.core.models.loader.generic_routes import create_api_router
from src.core.models.loader.generic_controller import create_controller

# Імпорт інструментів для автоматичного виявлення моделей з підтримкою універсальних маршрутів
from src.core.models.loader.generic_module_loader import discover_and_create_generic_routes
from src.core.models.loader.registry import get_model_by_name, get_all_models

# Головний API роутер
api_router = APIRouter(prefix=API_VERSION_PREFIX)

# Публічні ендпоінти (без необхідності автентифікації)
public_router = APIRouter()

# Ендпоінти, що вимагають авторизації
protected_router = APIRouter(dependencies=[Depends(require_auth)])

# Ендпоінти, що доступні лише для адміністраторів
admin_router = APIRouter(dependencies=[Depends(get_current_admin_user)])

# Включаємо публічні ендпоінти
api_router.include_router(public_router)

# Автоматично створюємо універсальні маршрути для моделей з атрибутом use_generic_routes=True
try:
    discover_and_create_generic_routes(api_router)
except Exception as e:
    import logging

    logging.error(f"Помилка при автоматичному створенні універсальних маршрутів: {e}")

# Додаємо існуючі маршрути, які не обробляються автоматично
# або мають специфічні вимоги щодо обробки

# Додаємо адміністративні роутери для спеціальних ендпоінтів
admin_router.include_router(logs_router, prefix="/logs")

# Додаємо захищений і адмін роутери до основного API
api_router.include_router(protected_router)
api_router.include_router(admin_router)

# Користувачі - комплексний роутер з різними рівнями доступу
# Примітка: ця частина може бути замінена автоматичною генерацією,
# якщо модель User має атрибут use_generic_routes=True
api_router.include_router(users_router, prefix="/users")


# Публічний ендпоінт для перевірки доступності API
@public_router.get("/health")
async def health_check():
    """
    Перевірка доступності API.
    """
    return {"status": "ok", "message": "API is running"}


# Захищений ендпоінт для тестування автентифікації
@protected_router.get("/auth-test")
async def auth_test(current_user: dict = Depends(require_auth)):
    """
    Тестовий ендпоінт для перевірки автентифікації.
    """
    return {
        "status": "authenticated",
        "message": "You are authenticated!",
        "user_id": current_user.get("sub"),
        "email": current_user.get("email"),
    }


# Адміністративний ендпоінт для тестування доступу
@admin_router.get("/admin-test")
async def admin_test(current_user: dict = Depends(get_current_admin_user)):
    """
    Тестовий ендпоінт для перевірки адміністративних прав.
    """
    return {
        "status": "admin",
        "message": "You have admin access!",
        "user_id": current_user.get("sub"),
        "email": current_user.get("email"),
    }
