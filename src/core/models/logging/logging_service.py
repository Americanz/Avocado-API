"""
Оптимізований сервіс логування з двома основними таблицями
"""

from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import json

from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import Depends

from src.core.models.logging.model import ApplicationLog, HttpLog
from src.core.models.logging.constants import LogLevel, LogDetailType, LogType
from src.core.database.connection import get_db


class OptimizedLoggingService:
    """Сервіс для логування з використанням оптимізованих таблиць"""

    _warning_shown = False  # Статична змінна для уникнення дублювання попереджень

    def __init__(self, db=None):
        """
        Ініціалізує сервіс логування.

        Args:
            db: Сесія бази даних або Depends(get_db)
        """
        # Перевіряємо, чи db є об'єктом Depends
        if db is None or db.__class__.__name__ == "Depends":
            # Використовуємо статичну змінну класу для уникнення дублювання повідомлень
            if not hasattr(OptimizedLoggingService, "_warning_shown"):
                print(
                    "Увага: Сесія бази даних є об'єктом Depends або None. Логування в БД буде пропущено."
                )
                OptimizedLoggingService._warning_shown = True
            # В режимі без БД або коли db - це Depends, створюємо заглушку
            self.db = None
        else:
            # В іншому випадку використовуємо надану сесію
            self.db = db

    # Методи для роботи з ApplicationLog

    def log_message(
        self,
        message: str,
        level: Union[LogLevel, str] = LogLevel.INFO,
        module: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Optional[ApplicationLog]:
        """
        Логує загальне повідомлення.

        Args:
            message: Повідомлення для логування
            level: Рівень логу
            module: Назва модуля
            data: Додаткові дані в форматі словника

        Returns:
            Створений запис ApplicationLog або None у випадку помилки
        """
        if self.db is None:
            # Якщо БД недоступна, просто виводимо повідомлення в консоль
            print(
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {level if isinstance(level, str) else level.value} | {module or 'Unknown'}: {message}"
            )
            return None

        try:
            # Створюємо запис логу
            log_entry = ApplicationLog.create_system_log(
                message=message, level=level, module=module, data=data
            )

            # Перевіряємо чи сесія асинхронна
            db_class_name = self.db.__class__.__name__
            if "Async" in db_class_name:
                # Для асинхронних сесій просто виводимо попередження - такі операції повинні
                # виконуватись в асинхронному контексті
                print(
                    f"Warning: Attempting to log to an async database session from a sync context. Message: {message}"
                )
                return None

            # Для синхронних сесій виконуємо нормальні операції
            self.db.add(log_entry)
            self.db.commit()
            self.db.refresh(log_entry)
            return log_entry
        except Exception as e:
            # Обробка помилки, наприклад, якщо таблиця не існує
            print(f"Error logging message: {e}")
            print(
                f"Message was: [{level if isinstance(level, str) else level.value}] {module or 'Unknown'}: {message}"
            )
            if "no such table" in str(e):
                print(
                    "Database tables for logging don't exist yet. Run migrations to create them."
                )
            try:
                if not "Async" in self.db.__class__.__name__:
                    self.db.rollback()
            except:
                pass
            return None

    def log_user_action(
        self,
        message: str,
        user_id: str,
        detail_type: Optional[Union[LogDetailType, str]] = None,
        level: Union[LogLevel, str] = LogLevel.INFO,
        module: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Optional[ApplicationLog]:
        """
        Логує дію користувача.

        Args:
            message: Опис дії
            user_id: ID користувача
            detail_type: Тип деталей (CREATE, UPDATE, DELETE, LOGIN)
            level: Рівень логу
            module: Назва модуля
            data: Додаткові дані

        Returns:
            Створений запис ApplicationLog або None у випадку помилки
        """
        if self.db is None:
            # Якщо БД недоступна, просто виводимо повідомлення в консоль
            print(
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {level if isinstance(level, str) else level.value} | User {user_id}: {message}"
            )
            return None

        try:
            log_entry = ApplicationLog.create_user_log(
                message=message,
                user_id=user_id,
                detail_type=detail_type,
                level=level,
                module=module,
                data=data,
            )

            self.db.add(log_entry)
            self.db.commit()
            self.db.refresh(log_entry)
            return log_entry
        except Exception as e:
            # Print the error to console since we can't log it to the database
            print(f"Error logging user action: {e}")
            print(
                f"Action: [{level if isinstance(level, str) else level.value}] User {user_id}: {message}"
            )
            if "no such table" in str(e):
                print(
                    "Database tables for logging don't exist yet. Run migrations to create them."
                )
            try:
                self.db.rollback()
            except:
                pass
            return None

    def log_error(
        self,
        message: str,
        exception: Optional[Exception] = None,
        module: Optional[str] = None,
        user_id: Optional[str] = None,
        http_log_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Optional[ApplicationLog]:
        """
        Логує помилку.

        Args:
            message: Повідомлення про помилку
            exception: Об'єкт виключення
            module: Назва модуля
            user_id: ID користувача (якщо відомий)
            http_log_id: ID HTTP логу (якщо помилка пов'язана з HTTP запитом)
            data: Додаткові дані

        Returns:
            Створений запис ApplicationLog або None у випадку помилки
        """
        if self.db is None:
            # Якщо БД недоступна, просто виводимо повідомлення в консоль
            import traceback

            error_trace = (
                "".join(
                    traceback.format_exception(
                        type(exception), exception, exception.__traceback__
                    )
                )
                if exception
                else ""
            )
            print(
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | ERROR | {module or 'Unknown'}: {message}"
            )
            if exception:
                print(f"Exception: {type(exception).__name__}: {str(exception)}")
                print(
                    f"Trace: {error_trace[:500]}{'...' if len(error_trace) > 500 else ''}"
                )
            return None

        try:
            log_entry = ApplicationLog.create_error_log(
                message=message,
                exception=exception,
                module=module,
                user_id=user_id,
                http_log_id=http_log_id,
                data=data,
            )

            self.db.add(log_entry)
            self.db.commit()
            self.db.refresh(log_entry)
            return log_entry
        except Exception as e:
            # Print the error to console since we can't log it to the database
            import traceback

            error_trace = (
                "".join(
                    traceback.format_exception(
                        type(exception), exception, exception.__traceback__
                    )
                )
                if exception
                else ""
            )
            print(f"Error while logging an error: {e}")
            print(f"Original error message: [{module or 'Unknown'}] {message}")
            print(
                f"Original exception: {type(exception).__name__ if exception else 'None'}"
            )
            print(
                f"Error trace: {error_trace[:500]}{'...' if len(error_trace) > 500 else ''}"
            )
            if "no such table" in str(e):
                print(
                    "Database tables for logging don't exist yet. Run migrations to create them."
                )
            try:
                self.db.rollback()
            except:
                pass
            return None

    def log_db_operation(
        self,
        message: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        detail_type: Optional[Union[LogDetailType, str]] = None,
        level: Union[LogLevel, str] = LogLevel.INFO,
        data: Optional[Dict[str, Any]] = None,
    ) -> Optional[ApplicationLog]:
        """
        Логує операцію з базою даних.

        Args:
            message: Опис операції
            entity_type: Тип сутності (таблиці)
            entity_id: ID сутності
            user_id: ID користувача, який виконав операцію
            detail_type: Тип операції (CREATE, UPDATE, DELETE)
            level: Рівень логу
            data: Додаткові дані (наприклад, старі та нові значення)

        Returns:
            Створений запис ApplicationLog або None у випадку помилки
        """
        if self.db is None:
            # Якщо БД недоступна, просто виводимо повідомлення в консоль
            print(
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {level if isinstance(level, str) else level.value} | DB {entity_type} {entity_id or '<no id>'}: {message}"
            )
            return None

        try:
            log_entry = ApplicationLog.create_db_log(
                message=message,
                entity_type=entity_type,
                entity_id=entity_id,
                user_id=user_id,
                detail_type=detail_type,
                level=level,
                data=data,
            )

            self.db.add(log_entry)
            self.db.commit()
            self.db.refresh(log_entry)
            return log_entry
        except Exception as e:
            print(f"Error logging database operation: {e}")
            print(
                f"Operation: [{level if isinstance(level, str) else level.value}] {entity_type} {entity_id or '<no id>'}: {message}"
            )
            if "no such table" in str(e):
                print(
                    "Database tables for logging don't exist yet. Run migrations to create them."
                )
            try:
                self.db.rollback()
            except:
                pass
            return None

    # Методи для роботи з HttpLog

    def log_request(
        self,
        method: str,
        path: str,
        client_ip: str,
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        body: Optional[Any] = None,
        user_id: Optional[str] = None,
    ) -> Optional[HttpLog]:
        """
        Логує HTTP запит.

        Args:
            method: HTTP метод (GET, POST, PUT, DELETE)
            path: Шлях запиту
            client_ip: IP-адреса клієнта
            headers: Заголовки запиту
            query_params: Параметри запиту
            body: Тіло запиту
            user_id: ID користувача (якщо авторизований)

        Returns:
            Створений запис HttpLog або None у випадку помилки
        """
        if self.db is None:
            # Якщо БД недоступна, просто виводимо повідомлення в консоль
            print(
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | HTTP REQUEST | {method} {path} from {client_ip}, user: {user_id or 'Anonymous'}"
            )
            return None

        try:
            # Приховуємо чутливі дані
            safe_headers = self._sanitize_headers(headers) if headers else None
            safe_body = self._sanitize_body(body) if body else None

            log_entry = HttpLog.create_request_log(
                method=method,
                path=path,
                client_ip=client_ip,
                headers=safe_headers,
                query_params=query_params,
                body=safe_body,
                user_id=user_id,
            )

            self.db.add(log_entry)
            self.db.commit()
            self.db.refresh(log_entry)
            return log_entry
        except Exception as e:
            print(f"Error logging HTTP request: {e}")
            print(
                f"Request: {method} {path} from {client_ip}, user_id: {user_id or 'Anonymous'}"
            )
            if "no such table" in str(e):
                print(
                    "Database tables for logging don't exist yet. Run migrations to create them."
                )
            try:
                self.db.rollback()
            except:
                pass
            return None

    def log_response(
        self,
        request_log_id: str,
        status_code: int,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Any] = None,
        processing_time_ms: Optional[float] = None,
    ) -> Optional[HttpLog]:
        """
        Логує HTTP відповідь.

        Args:
            request_log_id: ID запису логу запиту
            status_code: HTTP статус код
            headers: Заголовки відповіді
            body: Тіло відповіді
            processing_time_ms: Час обробки в мілісекундах

        Returns:
            Створений запис HttpLog або None у випадку помилки
        """
        if self.db is None:
            # Якщо БД недоступна, просто виводимо повідомлення в консоль
            print(
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | HTTP RESPONSE | Status {status_code} for request {request_log_id}"
            )
            return None

        try:
            # Приховуємо чутливі дані
            safe_headers = self._sanitize_headers(headers) if headers else None
            safe_body = self._sanitize_body(body) if body else None

            log_entry = HttpLog.create_response_log(
                request_log_id=request_log_id,
                status_code=status_code,
                headers=safe_headers,
                body=safe_body,
                processing_time_ms=processing_time_ms,
            )

            self.db.add(log_entry)
            self.db.commit()
            self.db.refresh(log_entry)
            return log_entry
        except Exception as e:
            print(f"Error logging HTTP response: {e}")
            print(f"Response: status {status_code} for request {request_log_id}")
            if "no such table" in str(e):
                print(
                    "Database tables for logging don't exist yet. Run migrations to create them."
                )
            try:
                self.db.rollback()
            except:
                pass
            return None

    # Методи для отримання логів

    def get_application_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        log_type: Optional[Union[LogType, str]] = None,
        level: Optional[Union[LogLevel, str]] = None,
        module: Optional[str] = None,
        user_id: Optional[str] = None,
        detail_type: Optional[Union[LogDetailType, str]] = None,
        entity_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[ApplicationLog]:
        """
        Отримує системні логи з фільтрацією.

        Args:
            limit: Максимальна кількість записів
            offset: Кількість записів, які потрібно пропустити
            log_type: Тип логу (SYSTEM, USER, DATABASE, ERROR)
            level: Рівень логу
            module: Фільтр за назвою модуля
            user_id: Фільтр за ID користувача
            detail_type: Фільтр за типом деталей
            entity_type: Фільтр за типом сутності (для логів БД)
            start_date: Фільтр за датою (від)
            end_date: Фільтр за датою (до)

        Returns:
            Список записів ApplicationLog
        """
        query = self.db.query(ApplicationLog)

        # Застосовуємо фільтри
        if log_type is not None:
            log_type_val = log_type.value if hasattr(log_type, "value") else log_type
            query = query.filter(ApplicationLog.log_type == log_type_val)

        if level is not None:
            level_val = level.value if hasattr(level, "value") else level
            query = query.filter(ApplicationLog.level == level_val)

        if module is not None:
            query = query.filter(ApplicationLog.module == module)

        if user_id is not None:
            query = query.filter(ApplicationLog.user_id == user_id)

        if detail_type is not None:
            detail_type_val = (
                detail_type.value if hasattr(detail_type, "value") else detail_type
            )
            query = query.filter(ApplicationLog.detail_type == detail_type_val)

        if entity_type is not None:
            query = query.filter(ApplicationLog.entity_type == entity_type)

        if start_date is not None:
            query = query.filter(ApplicationLog.timestamp >= start_date)

        if end_date is not None:
            query = query.filter(ApplicationLog.timestamp <= end_date)

        # Сортування за часом у спадному порядку (найновіші спочатку)
        query = query.order_by(desc(ApplicationLog.timestamp))

        # Пагінація
        query = query.limit(limit).offset(offset)

        return query.all()

    def get_http_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        is_request: Optional[bool] = None,
        method: Optional[str] = None,
        path: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_id: Optional[str] = None,
        status_code: Optional[int] = None,
        min_processing_time: Optional[float] = None,
        max_processing_time: Optional[float] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[HttpLog]:
        """
        Отримує HTTP логи з фільтрацією.

        Args:
            limit: Максимальна кількість записів
            offset: Кількість записів, які потрібно пропустити
            is_request: Фільтр за типом (True - запити, False - відповіді)
            method: Фільтр за HTTP методом
            path: Фільтр за шляхом
            client_ip: Фільтр за IP клієнта
            user_id: Фільтр за ID користувача
            status_code: Фільтр за HTTP статус кодом
            min_processing_time: Мінімальний час обробки
            max_processing_time: Максимальний час обробки
            start_date: Фільтр за датою (від)
            end_date: Фільтр за датою (до)

        Returns:
            Список записів HttpLog
        """
        query = self.db.query(HttpLog)

        # Застосовуємо фільтри
        if is_request is not None:
            query = query.filter(HttpLog.is_request == is_request)

        if method is not None:
            query = query.filter(HttpLog.method == method)

        if path is not None:
            query = query.filter(HttpLog.path.like(f"%{path}%"))

        if client_ip is not None:
            query = query.filter(HttpLog.client_ip == client_ip)

        if user_id is not None:
            query = query.filter(HttpLog.user_id == user_id)

        if status_code is not None:
            query = query.filter(HttpLog.status_code == status_code)

        if min_processing_time is not None:
            query = query.filter(HttpLog.processing_time_ms >= min_processing_time)

        if max_processing_time is not None:
            query = query.filter(HttpLog.processing_time_ms <= max_processing_time)

        if start_date is not None:
            query = query.filter(HttpLog.timestamp >= start_date)

        if end_date is not None:
            query = query.filter(HttpLog.timestamp <= end_date)

        # Сортування за часом у спадному порядку (найновіші спочатку)
        query = query.order_by(desc(HttpLog.timestamp))

        # Пагінація
        query = query.limit(limit).offset(offset)

        return query.all()

    def get_request_with_response(self, request_id: str) -> Dict[str, Any]:
        """
        Отримує запит та пов'язану з ним відповідь.

        Args:
            request_id: ID запису запиту

        Returns:
            Словник з даними запиту та відповіді
        """
        request_log = self.db.query(HttpLog).filter(HttpLog.id == request_id).first()
        if not request_log:
            return None

        # Знаходимо відповідь, якщо вона є
        response_log = (
            self.db.query(HttpLog)
            .filter(HttpLog.related_log_id == request_id, HttpLog.is_request == False)
            .first()
        )

        result = {
            "request": {
                "id": request_log.id,
                "timestamp": request_log.timestamp,
                "method": request_log.method,
                "path": request_log.path,
                "client_ip": request_log.client_ip,
                "user_id": request_log.user_id,
                "headers": request_log.request_headers,
                "query_params": request_log.query_params,
                "body": request_log.request_body,
            },
            "response": None,
        }

        if response_log:
            result["response"] = {
                "id": response_log.id,
                "timestamp": response_log.timestamp,
                "status_code": response_log.status_code,
                "headers": response_log.response_headers,
                "body": response_log.response_body,
                "processing_time_ms": response_log.processing_time_ms,
            }

        return result

    # Допоміжні методи

    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        Видаляє чутливу інформацію з заголовків.

        Args:
            headers: Словник заголовків

        Returns:
            Очищений словник заголовків
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
            Очищене тіло
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
