"""
Сервіс логування з використанням loguru та інтеграцією з БД через оптимізований сервіс логування
"""

from typing import Optional, Dict, Any
import sys
import json
import traceback

from loguru import logger
from sqlalchemy import text

from src.core.models.logging.constants import LogLevel
from src.core.models.logging.logging_service import OptimizedLoggingService


# Налаштування loguru
def setup_logger():
    """Налаштування loguru з виводом в консоль та файл"""
    # Видаляємо стандартний обробник
    logger.remove()

    # Додаємо обробник для виводу в консоль
    logger.add(
        sys.stderr,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO",
    )

    # Додаємо обробник для запису в один файл за день
    logger.add(
        "logs/application_{time:YYYY-MM-DD}.log",
        rotation="00:00",  # Ротація о опівночі - новий файл щодня
        retention="14 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="DEBUG",
    )


# Викликаємо налаштування loguru при імпорті модуля
setup_logger()


class OptimizedLoguruService:
    """Сервіс для логування з використанням loguru та оптимізованих таблиць"""

    def __init__(self, db_service: Optional[OptimizedLoggingService] = None):
        """
        Ініціалізує сервіс з інтеграцією loguru.

        Args:
            db_service: Опціональний сервіс для логування в БД
        """
        self.db_service = db_service
        self._db_available = False

        # Перевіряємо доступність бази даних для логування
        if self.db_service:
            try:
                self._check_db_available()
            except Exception as e:
                # Якщо виникла помилка, виводимо повідомлення та вимикаємо логування в базу даних
                print(
                    f"Увага: Логування в базу даних вимкнено. Помилка: {e}",
                    file=sys.stderr,
                )
                self.db_service = None

    def _check_db_available(self) -> bool:
        """
        Перевіряє, чи доступна база даних.

        Returns:
            bool: True якщо база даних доступна, False в іншому випадку
        """
        if not self.db_service or not self.db_service.db:
            return False

        try:
            # Перевіряємо тип бази даних, щоб використовувати правильний виклик
            # Якщо це асинхронна сесія, ми не можемо її перевірити в синхронному контексті
            db_class_name = self.db_service.db.__class__.__name__
            if 'Async' in db_class_name:
                # Для асинхронних сесій просто припускаємо, що база даних доступна
                # оскільки ми не можемо викликати await в синхронному методі
                return True
            else:
                # Для синхронних сесій перевіряємо доступність
                result = self.db_service.db.execute(text("SELECT 1")).scalar()
                return result == 1
        except Exception as e:
            self._handle_exception(e, "Failed to check database availability")
            return False

    def debug(
        self,
        message: str,
        module: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ):
        """
        Логує повідомлення рівня DEBUG.

        Args:
            message: Повідомлення для логування
            module: Назва модуля
            data: Додаткові дані
        """
        log_data = self._format_log_data(data)
        logger.debug(f"{module or ''}: {message} {log_data}")

        if self.db_service:
            self.db_service.log_message(message, LogLevel.DEBUG, module, data)

    def info(
        self,
        message: str,
        module: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ):
        """
        Логує повідомлення рівня INFO.

        Args:
            message: Повідомлення для логування
            module: Назва модуля
            data: Додаткові дані
        """
        log_data = self._format_log_data(data)
        logger.info(f"{module or ''}: {message} {log_data}")

        if self.db_service:
            self.db_service.log_message(message, LogLevel.INFO, module, data)

    def warning(
        self,
        message: str,
        module: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ):
        """
        Логує повідомлення рівня WARNING.

        Args:
            message: Повідомлення для логування
            module: Назва модуля
            data: Додаткові дані
        """
        log_data = self._format_log_data(data)
        logger.warning(f"{module or ''}: {message} {log_data}")

        if self.db_service:
            self.db_service.log_message(message, LogLevel.WARNING, module, data)

    def error(
        self,
        message: str,
        exception: Optional[Exception] = None,
        module: Optional[str] = None,
        http_log_id: Optional[str] = None,
        user_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ):
        """
        Логує повідомлення рівня ERROR.

        Args:
            message: Повідомлення для логування
            exception: Виключення, якщо є
            module: Назва модуля
            http_log_id: ID HTTP логу, якщо помилка пов'язана з HTTP запитом
            user_id: ID користувача, якщо відомий
            data: Додаткові дані
        """
        log_data = self._format_log_data(data)

        if exception:
            logger.exception(f"{module or ''}: {message} {log_data}")
        else:
            logger.error(f"{module or ''}: {message} {log_data}")

        if self.db_service:
            self.db_service.log_error(
                message=message,
                exception=exception,
                module=module,
                user_id=user_id,
                http_log_id=http_log_id,
                data=data,
            )

    def critical(
        self,
        message: str,
        exception: Optional[Exception] = None,
        module: Optional[str] = None,
        http_log_id: Optional[str] = None,
        user_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ):
        """
        Логує повідомлення рівня CRITICAL.

        Args:
            message: Повідомлення для логування
            exception: Виключення, якщо є
            module: Назва модуля
            http_log_id: ID HTTP логу, якщо помилка пов'язана з HTTP запитом
            user_id: ID користувача, якщо відомий
            data: Додаткові дані
        """
        log_data = self._format_log_data(data)

        if exception:
            logger.exception(f"{module or ''}: {message} {log_data}")
        else:
            logger.critical(f"{module or ''}: {message} {log_data}")

        if self.db_service:
            self.db_service.log_error(
                message=message,
                exception=exception,
                module=module,
                user_id=user_id,
                http_log_id=http_log_id,
                data=data,
                level=LogLevel.CRITICAL,
            )

    def log_user_action(
        self,
        message: str,
        user_id: str,
        detail_type: Optional[str] = None,
        module: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        level: LogLevel = LogLevel.INFO,
    ):
        """
        Логує дію користувача.

        Args:
            message: Опис дії
            user_id: ID користувача
            detail_type: Тип дії (CREATE, UPDATE, DELETE, тощо)
            module: Назва модуля
            data: Додаткові дані
            level: Рівень логування
        """
        log_data = self._format_log_data(data)

        # Логуємо в loguru з відповідним рівнем
        if level == LogLevel.DEBUG:
            logger.debug(f"{module or ''}: User {user_id} - {message} {log_data}")
        elif level == LogLevel.INFO:
            logger.info(f"{module or ''}: User {user_id} - {message} {log_data}")
        elif level == LogLevel.WARNING:
            logger.warning(f"{module or ''}: User {user_id} - {message} {log_data}")
        elif level == LogLevel.ERROR:
            logger.error(f"{module or ''}: User {user_id} - {message} {log_data}")
        elif level == LogLevel.CRITICAL:
            logger.critical(f"{module or ''}: User {user_id} - {message} {log_data}")

        # Логуємо в БД, якщо сервіс доступний
        if self.db_service:
            self.db_service.log_user_action(
                message=message,
                user_id=user_id,
                detail_type=detail_type,
                level=level,
                module=module,
                data=data,
            )

    def log_request(
        self,
        method: str,
        path: str,
        client_ip: str,
        headers: Dict[str, str] = None,
        query_params: Dict[str, str] = None,
        body: Any = None,
        user_id: Optional[str] = None,
    ):
        """
        Логує HTTP запит.

        Args:
            method: HTTP метод
            path: Шлях запиту
            client_ip: IP клієнта
            headers: Заголовки запиту
            query_params: Параметри запиту
            body: Тіло запиту
            user_id: ID користувача, якщо авторизований

        Returns:
            HttpLog: Запис логу або None, якщо БД недоступна
        """
        # Приховуємо чутливі дані для консольного логування
        safe_headers = self._sanitize_headers(headers) if headers else None
        safe_body = self._sanitize_body(body) if body else None

        # Форматуємо дані для loguru
        log_message = (
            f"HTTP Request: {method} {path} from {client_ip} "
            f"User: {user_id or 'anonymous'}"
        )

        # Додаємо детальну інформацію для loguru
        detail = {
            "method": method,
            "path": path,
            "client_ip": client_ip,
            "user_id": user_id,
            "headers": safe_headers,
            "query_params": query_params,
            "body": safe_body,
        }

        # Логуємо через loguru
        logger.info(f"{log_message} {self._format_log_data(detail)}")

        # Якщо є сервіс для БД, зберігаємо там теж
        if self.db_service:
            return self.db_service.log_request(
                method=method,
                path=path,
                client_ip=client_ip,
                headers=headers,
                query_params=query_params,
                body=body,
                user_id=user_id,
            )
        return None

    def _format_log_data(self, data: Optional[Dict[str, Any]]) -> str:
        """
        Форматує додаткові дані для логування.

        Args:
            data: Словник з додатковими даними

        Returns:
            str: Відформатований рядок
        """
        if not data:
            return ""
        try:
            return json.dumps(data, default=str, ensure_ascii=False)
        except Exception:
            return str(data)

    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        Видаляє чутливу інформацію з заголовків.

        Args:
            headers: Словник заголовків

        Returns:
            Dict[str, str]: Очищений словник заголовків
        """
        if not headers:
            return {}

        sensitive_headers = ["authorization", "cookie", "set-cookie"]
        safe_headers = {}

        for key, value in headers.items():
            key_lower = key.lower()
            if key_lower in sensitive_headers:
                safe_headers[key] = "[REDACTED]"
            else:
                safe_headers[key] = value

        return safe_headers

    def _sanitize_body(self, body: Any) -> Any:
        """
        Видаляє чутливу інформацію з тіла запиту/відповіді.

        Args:
            body: Тіло запиту або відповіді

        Returns:
            Any: Очищене тіло
        """
        if not body:
            return body

        # Якщо тіло - словник, прибираємо чутливі дані
        if isinstance(body, dict):
            safe_body = {}
            sensitive_fields = [
                "password",
                "token",
                "secret",
                "credit_card",
                "card_number",
                "key",
                "api_key",
                "access_token",
                "refresh_token",
            ]

            for key, value in body.items():
                key_lower = str(key).lower()
                if any(sensitive in key_lower for sensitive in sensitive_fields):
                    safe_body[key] = "[REDACTED]"
                elif isinstance(value, dict):
                    safe_body[key] = self._sanitize_body(value)
                elif isinstance(value, list) and all(
                    isinstance(item, dict) for item in value
                ):
                    safe_body[key] = [self._sanitize_body(item) for item in value]
                else:
                    safe_body[key] = value

            return safe_body

        return body

    def log_response(
        self,
        request_log_id: Optional[str],
        status_code: int,
        headers: Dict[str, str] = None,
        body: Any = None,
        processing_time_ms: Optional[float] = None,
    ):
        """
        Логує HTTP відповідь.

        Args:
            request_log_id: ID відповідного запису запиту
            status_code: HTTP статус код
            headers: Заголовки відповіді
            body: Тіло відповіді
            processing_time_ms: Час обробки в мілісекундах

        Returns:
            HttpLog: Запис логу або None, якщо БД недоступна
        """
        # Приховуємо чутливі дані для консольного логування
        safe_headers = self._sanitize_headers(headers) if headers else None
        safe_body = self._sanitize_body(body) if body else None

        # Форматуємо дані для loguru
        log_message = (
            f"HTTP Response: Status {status_code} " f"Time: {processing_time_ms:.2f}ms"
            if processing_time_ms
            else f"HTTP Response: Status {status_code}"
        )

        # Додаємо детальну інформацію для loguru
        detail = {
            "status_code": status_code,
            "processing_time_ms": processing_time_ms,
            "headers": safe_headers,
            "body": safe_body,
        }

        # Визначаємо рівень логування в залежності від статус-коду
        if status_code >= 500:
            logger.error(f"{log_message} {self._format_log_data(detail)}")
        elif status_code >= 400:
            logger.warning(f"{log_message} {self._format_log_data(detail)}")
        else:
            logger.info(f"{log_message} {self._format_log_data(detail)}")

        # Якщо є сервіс для БД і є ID запиту, зберігаємо там теж
        if self.db_service and request_log_id:
            return self.db_service.log_response(
                request_log_id=request_log_id,
                status_code=status_code,
                headers=headers,
                body=body,
                processing_time_ms=processing_time_ms,
            )
        return None
