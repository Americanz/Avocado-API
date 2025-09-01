"""
Main FastAPI application.
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from src.config import settings
from src.config.constants import API_VERSION_PREFIX
from src.core.database.connection import init_db
from src.core.exceptions.handlers import add_exception_handlers
from src.config.redis import get_redis_client

# Імпортуємо middleware для логування з правильного місця
from src.core.models.logging.middleware import OptimizedRequestLoggingMiddleware
from src.core.loader_factory.registry_factory.registry import register_all_models
from src.core.loader_factory.registry_factory.loader import setup_app_modules

# Імпортуємо наші нові сервіси логування
from src.core.models.logging.loguru_service import OptimizedLoguruService
from src.core.models.logging.logging_service import OptimizedLoggingService
from src.core.models.logging.providers import set_global_logger

# Імпортуємо функцію для перевірки міграцій
from src.core.database.migrations import has_pending_migrations

# Налаштовуємо рівень логування для SQLAlchemy
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# Глобальна змінна для зберігання логера
app_logger = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan event handler.

    Args:
        app: FastAPI application
    """
    global app_logger

    # Ініціалізація бази даних
    db_session = await init_db()

    # Ініціалізація Redis та збереження в app.state
    redis_client = get_redis_client()
    app.state.redis = redis_client

    # Перевірка наявності нових міграцій
    if has_pending_migrations():
        print("⚠️  УВАГА: В базі даних є незастосовані міграції!")
        print("⚠️  Запустіть 'alembic upgrade head' для застосування міграцій.")

    # Налаштування loguru з записом у БД
    try:
        # Створюємо синхронну сесію для логування замість асинхронної
        from src.core.database.connection import get_sync_db

        sync_db_session = get_sync_db()

        # Зберігаємо сесію в стані додатку для використання в middleware
        app.state.db_session = sync_db_session

        # Використовуємо синхронну сесію для логера
        db_logger = OptimizedLoggingService(db=sync_db_session)
        app_logger = OptimizedLoguruService(db_service=db_logger)

        # Встановлюємо глобальний логер для доступу з будь-якого місця
        set_global_logger(app_logger)

        # Логуємо початок роботи програми через наш логер
        app_logger.info(
            "Application startup completed",
            module="app.startup",
            data={"app_name": settings.APP_NAME, "environment": settings.ENVIRONMENT},
        )
    except Exception as e:
        # Якщо не вдалося створити логер, друкуємо помилку в консоль
        print(f"Error setting up logger: {e}")
        raise

    # Завантаження демо-даних, якщо потрібно
    from src.core.services.demo_data import load_demo_data

    await load_demo_data(db_session)

    yield

    # Shutdown
    if app_logger:
        app_logger.info("Shutting down application...", module="app.shutdown")

        # Закриваємо синхронну сесію при завершенні
        try:
            sync_db_session.close()
        except:
            pass

    # Закриття Redis (якщо потрібно)
    if hasattr(redis_client, 'close'):
        redis_client.close()


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application
    """
    # Реєструємо всі моделі перед створенням застосунку
    register_all_models()

    # Визначаємо URL для документації в залежності від налаштувань
    docs_url = "/docs" if settings.ENABLE_SWAGGER else None
    redoc_url = "/redoc" if settings.ENABLE_REDOC else None
    openapi_url = (
        "/openapi.json" if (settings.ENABLE_SWAGGER or settings.ENABLE_REDOC) else None
    )

    # Create FastAPI app
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_methods=settings.CORS_METHODS,
        allow_headers=settings.CORS_HEADERS,
        allow_credentials=True,
    )

    # Add new logging middleware
    app.add_middleware(
        OptimizedRequestLoggingMiddleware,
        excluded_paths=["/docs", "/openapi.json", "/redoc", "/metrics", "/health"],
    )

    # Налаштування та реєстрація всіх модулів
    setup_app_modules(app, API_VERSION_PREFIX)

    # Add exception handlers
    add_exception_handlers(app)

    # Customize OpenAPI schema
    if openapi_url:

        def custom_openapi():
            if app.openapi_schema:
                return app.openapi_schema

            openapi_schema = get_openapi(
                title=settings.APP_NAME,
                version=settings.APP_VERSION,
                description=settings.APP_DESCRIPTION,
                routes=app.routes,
            )

            # Можете додати додаткову інформацію до схеми OpenAPI тут
            openapi_schema["info"]["contact"] = {
                "name": "Support",
                "email": "support@avocado.example.com",
            }

            # Додаємо компонент безпеки для API токена
            openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})

            # Налаштування JWT Bearer Token
            openapi_schema["components"]["securitySchemes"]["bearerAuth"] = {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Введіть ваш JWT токен у форматі: Bearer {token}"
            }

            # Налаштування API Key
            openapi_schema["components"]["securitySchemes"]["apiKeyAuth"] = {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "Введіть ваш API токен"
            }

            # Глобальні налаштування безпеки для всіх ендпоінтів
            # Клієнт може використати або JWT, або API Key
            openapi_schema["security"] = [
                {"bearerAuth": []},
                {"apiKeyAuth": []}
            ]

            app.openapi_schema = openapi_schema
            return app.openapi_schema

        # Set custom OpenAPI schema
        app.openapi = custom_openapi

    return app


# Create app instance
app = create_app()
