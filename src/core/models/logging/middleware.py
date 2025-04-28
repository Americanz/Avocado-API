"""
Оптимізований middleware для логування запитів та відповідей
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
from typing import Callable, Dict, Any, List, Optional
import uuid
import inspect
import json
import asyncio

from src.core.models.logging.logging_service import OptimizedLoggingService
from src.core.common.ctx import request_id_contextvar, get_request_id, set_request_id
from src.core.database.connection import get_sync_db  # Залишаємо імпорт для аварійного випадку


class OptimizedRequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для логування всіх HTTP запитів та відповідей з використанням оптимізованих таблиць"""

    def __init__(self, app: ASGIApp, excluded_paths: List[str] = None):
        """
        Ініціалізує middleware.

        Args:
            app: ASGI додаток
            excluded_paths: Список шляхів, які не потрібно логувати
        """
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/docs",
            "/openapi.json",
            "/redoc",
            "/metrics",
            "/health",
            "/favicon.ico",
            "/_next",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Обробляє запит, логує його та відповідь.

        Args:
            request: Об'єкт запиту FastAPI
            call_next: Функція для виклику наступного обробника

        Returns:
            Response: Об'єкт відповіді
        """
        # Генеруємо унікальний ID запиту та зберігаємо його в контекстній змінній
        request_id = str(uuid.uuid4())
        set_request_id(request_id)

        # Пропускаємо логування для виключених шляхів
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.excluded_paths):
            response = await call_next(request)
            return response

        # Встановлюємо таймаут для запиту
        try:
            # Ініціалізуємо сервіс логування
            db_session = None
            should_close_db = False
            logging_service = None
            request_log = None
            start_time = time.time()

            try:
                # Використовуємо спільне підключення до БД з контексту, якщо воно є
                if hasattr(request.app.state, "db_session") and request.app.state.db_session:
                    db_session = request.app.state.db_session
                    should_close_db = False  # Не закриваємо, бо це спільне з'єднання
                else:
                    # Аварійний варіант: створюємо нове з'єднання, якщо спільного немає
                    db_session = get_sync_db()
                    should_close_db = True  # Потрібно закрити в кінці, оскільки ми його створили
                    print("Warning: Using fallback DB connection in middleware")

                logging_service = OptimizedLoggingService(db_session)

                # Отримуємо тіло запиту (якщо є)
                request_body = None
                if request.method in ["POST", "PUT", "PATCH"]:
                    try:
                        # Зберігаємо оригінальну функцію отримання тіла
                        original_receive = request.receive

                        # Читаємо тіло
                        body_bytes = await request.body()

                        # Створюємо новий receive, який повертає тіло
                        async def receive():
                            return {"type": "http.request", "body": body_bytes, "more_body": False}

                        # Перевизначаємо receive для запиту
                        request._receive = receive

                        if body_bytes:
                            try:
                                request_body = json.loads(body_bytes)
                            except:
                                request_body = {"raw": str(body_bytes)[:200]}
                    except Exception as e:
                        request_body = {"error": f"Failed to read request body: {str(e)}"}

                # Отримуємо IP клієнта
                client_host = request.client.host if request.client else "unknown"

                # Отримуємо ID авторизованого користувача (якщо є)
                user_id = None
                if hasattr(request.state, "user") and hasattr(request.state.user, "id"):
                    user_id = request.state.user.id

                # Логуємо запит
                request_log = logging_service.log_request(
                    method=request.method,
                    path=str(request.url.path),
                    client_ip=client_host,
                    headers=dict(request.headers),
                    query_params=dict(request.query_params),
                    body=request_body,
                    user_id=user_id,
                )

                # Зберігаємо ID логу запиту в контексті для обробки помилок
                request.state.request_log_id = request_log.id if request_log else None

            except Exception as ex:
                # Якщо не вдалося логувати запит, продовжуємо без логування
                print(f"Error logging request: {str(ex)}")

            # Обробляємо запит та вимірюємо час з таймаутом
            try:
                # Викликаємо наступний обробник
                response = await call_next(request)

                # Логуємо відповідь, тільки якщо запит було успішно заресстровано
                if logging_service and request_log:
                    try:
                        # Обчислюємо час обробки
                        process_time = time.time() - start_time
                        process_time_ms = round(process_time * 1000, 2)

                        # Отримуємо тіло відповіді
                        response_body = None

                        # Для streaming відповідей не отримуємо тіло
                        if not getattr(response, "background", None):
                            try:
                                response_body_bytes = response.body
                                try:
                                    response_body = json.loads(response_body_bytes)
                                except:
                                    # Якщо не JSON, зберігаємо перші 200 символів
                                    text = response_body_bytes.decode("utf-8", errors="replace")
                                    response_body = text[:200] + ("..." if len(text) > 200 else "")
                            except:
                                response_body = {"error": "Could not read response body"}

                        # Логуємо відповідь
                        logging_service.log_response(
                            request_log_id=request_log.id,
                            status_code=response.status_code,
                            headers=dict(response.headers),
                            body=response_body,
                            processing_time_ms=process_time_ms,
                        )

                        # Додаємо заголовок з часом обробки та ID запиту
                        response.headers["X-Process-Time"] = str(process_time_ms)
                        response.headers["X-Request-ID"] = request_id
                    except Exception as ex:
                        print(f"Error logging response: {str(ex)}")

                return response

            except Exception as ex:
                # Обробляємо помилку, але тільки якщо запит було успішно заресстровано
                if logging_service and request_log:
                    try:
                        # Обчислюємо час обробки до виникнення помилки
                        process_time = time.time() - start_time
                        process_time_ms = round(process_time * 1000, 2)

                        # Логуємо помилку
                        logging_service.log_error(
                            message=f"Помилка обробки запиту: {str(ex)}",
                            exception=ex,
                            module=(
                                inspect.getmodule(ex).__name__ if inspect.getmodule(ex) else None
                            ),
                            http_log_id=request_log.id,
                            data={
                                "processing_time_ms": process_time_ms,
                                "path": str(request.url.path),
                                "method": request.method,
                            },
                        )

                        # Логуємо відповідь помилки
                        logging_service.log_response(
                            request_log_id=request_log.id,
                            status_code=500,
                            headers={},
                            body={"detail": "Internal Server Error"},
                            processing_time_ms=process_time_ms,
                        )
                    except Exception as log_ex:
                        print(f"Error logging exception: {str(log_ex)}")

                # Перенаправляємо виключення для обробки обробниками помилок
                raise

        finally:
            # Закриваємо з'єднання з базою даних в кінці запиту, тільки якщо ми його створили
            try:
                if should_close_db and db_session:
                    db_session.close()
            except Exception as e:
                print(f"Error closing DB session: {str(e)}")
