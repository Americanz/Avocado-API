"""
Adapter for Loguru logger that supports both OptimizedLoguruService and legacy loguru styles.
"""

import logging
from typing import Any, Dict, Optional, Union

# Импортируем глобальный логгер
from src.core.models.logging.providers import get_global_logger


class LoggerAdapter:
    """
    Адаптер логирования, поддерживающий разные форматы вызова.
    Обеспечивает совместимость с loguru и OptimizedLoguruService.
    """

    def __init__(self, original_logger=None):
        """
        Инициализация адаптера с базовым логгером.

        Args:
            original_logger: Исходный логгер (default: глобальный логгер из providers.get_global_logger)
        """
        # Используем предоставленный логгер или получаем глобальный
        self.logger = original_logger or get_global_logger()

        # Если глобальный логгер не доступен, используем стандартный модуль logging
        if self.logger is None:
            self.standard_logger = logging.getLogger("checkbox_module")
            # Настройка обработчика для вывода в консоль
            if not self.standard_logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
                handler.setFormatter(formatter)
                self.standard_logger.addHandler(handler)
                self.standard_logger.setLevel(logging.INFO)

    def debug(self, *args, **kwargs):
        """Debug-уровень логирования с поддержкой разных форматов."""
        self._process_log("debug", *args, **kwargs)

    def info(self, *args, **kwargs):
        """Info-уровень логирования с поддержкой разных форматов."""
        self._process_log("info", *args, **kwargs)

    def warning(self, *args, **kwargs):
        """Warning-уровень логирования с поддержкой разных форматов."""
        self._process_log("warning", *args, **kwargs)

    def error(self, *args, **kwargs):
        """Error-уровень логирования с поддержкой разных форматов."""
        self._process_log("error", *args, **kwargs)

    def critical(self, *args, **kwargs):
        """Critical-уровень логирования с поддержкой разных форматов."""
        self._process_log("critical", *args, **kwargs)

    def _process_log(self, level, *args, **kwargs):
        """
        Обрабатывает вызов логирования, адаптируя аргументы под нужный формат.

        Args:
            level: Уровень логирования (debug, info, warning, error, critical)
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы
        """
        # Упрощенный случай, когда первый аргумент - строка сообщения
        if args and isinstance(args[0], str):
            message = args[0]
            # Получаем дополнительные аргументы
            module = kwargs.get("module")
            data = kwargs.get("data")
            exception = kwargs.get("exception") or kwargs.get("error")

            # Вызываем соответствующий метод в зависимости от уровня
            if level == "debug":
                getattr(self.logger, level)(message, module=module, data=data)
            elif level == "info":
                getattr(self.logger, level)(message, module=module, data=data)
            elif level == "warning":
                getattr(self.logger, level)(message, module=module, data=data)
            elif level == "error" or level == "critical":
                getattr(self.logger, level)(
                    message, exception=exception, module=module, data=data
                )

        # Случай с именованными аргументами для старого стиля (Checkbox)
        elif "message" in kwargs or "_Logger__message" in kwargs:
            # Извлекаем сообщение
            message = kwargs.get("message", kwargs.get("_Logger__message", ""))
            # Формируем дополнительную информацию
            component = kwargs.get("component", "")
            action = kwargs.get("action", "")

            # Создаем сообщение с контекстом
            context_message = (
                f"{component}:{action} - {message}" if component or action else message
            )

            # Извлекаем данные и ошибку
            data = kwargs.get("data", {})
            error = kwargs.get("error", None)

            # Вызываем соответствующий метод
            if level == "debug" or level == "info" or level == "warning":
                getattr(self.logger, level)(context_message, data=data)
            elif level == "error" or level == "critical":
                getattr(self.logger, level)(context_message, exception=error, data=data)

        # Если формат не распознан, просто передаем аргументы как есть
        else:
            # Безопасный вызов метода логгера с проверкой наличия метода
            log_method = getattr(self.logger, level, None)
            if callable(log_method):
                log_method(*args, **kwargs)
            else:
                # Запасной вариант с использованием стандартного модуля logging
                getattr(logging, level, logging.error)(" ".join(str(a) for a in args))


# Создаем глобальный экземпляр адаптера, который будет использоваться в модулях
checkbox_logger = LoggerAdapter()
