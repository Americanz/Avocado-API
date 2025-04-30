"""
Application settings module.
"""

import os
from pathlib import Path
from typing import List, Optional, Union

from dotenv import load_dotenv
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Завантаження змінних середовища з .env файлу
load_dotenv()

# Визначення базових шляхів проекту
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BASE_DIR = PROJECT_ROOT


class Settings(BaseSettings):
    """Application settings."""

    # Базові налаштування додатку
    APP_NAME: str = os.getenv("APP_NAME", "Avocado")
    APP_DESCRIPTION: str = os.getenv(
        "APP_DESCRIPTION",
        "Avocado is a web application for managing your tasks and projects.",
    )
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    API_PREFIX: str = os.getenv("API_PREFIX", "/api")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ["true", "1"]
    LOAD_DEMO_DATA: bool = os.getenv("LOAD_DEMO_DATA", "False").lower() in ["true", "1"]
    TIMEZONE: str = os.getenv("TIMEZONE", "UTC")

    # Налаштування сервера
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    # Шляхи до директорій
    PROJECT_ROOT: Path = PROJECT_ROOT
    BASE_DIR: Path = BASE_DIR
    LOGS_DIR: Path = BASE_DIR / "logs"
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")

    # Налаштування бази даних
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./database.db")
    ASYNC_DATABASE_URL: Optional[str] = os.getenv("ASYNC_DATABASE_URL", None)
    USE_SQLITE: bool = os.getenv("USE_SQLITE", "True").lower() in ["true", "1"]
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "sqlite:///./database.db")
    TEST_SQLITE_DB_PATH: str = os.getenv("TEST_SQLITE_DB_PATH", "sqlite:///./test.db")
    RESET_DB: bool = os.getenv("RESET_DB", "False").lower() in ["true", "1"]

    # Налаштування безпеки
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )

    # Налаштування аутентифікації
    ENABLE_PASSWORD_AUTH: bool = os.getenv("ENABLE_PASSWORD_AUTH", "True").lower() in [
        "true",
        "1",
    ]
    ENABLE_OTP_AUTH: bool = os.getenv("ENABLE_OTP_AUTH", "True").lower() in [
        "true",
        "1",
    ]
    ENABLE_SOCIAL_AUTH: bool = os.getenv("ENABLE_SOCIAL_AUTH", "False").lower() in [
        "true",
        "1",
    ]
    ENABLE_EMAIL_NOTIFICATIONS: bool = os.getenv(
        "ENABLE_EMAIL_NOTIFICATIONS", "False").lower() in [
        "true",
        "1",
    ]

    OTP_EXPIRY_MINUTES: int = int(
        os.getenv("OTP_EXPIRY_MINUTES", "15")
    )  # OTP действителен 15 минут по умолчанию
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("JWT_REFRESH_TOKEN_EXPIRE_MINUTES", "10080")
    )  # 7 days

    # Telegram Bot settings
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_AUTH_EXPIRY_MINUTES: int = int(os.getenv("TELEGRAM_AUTH_EXPIRY_MINUTES", "15"))
    ENABLE_TELEGRAM_AUTH: bool = os.getenv("ENABLE_TELEGRAM_AUTH", "true").lower() == "true"

    # Налаштування CORS
    CORS_ORIGINS: List[str] = ["*"]  # Буде перезаписано з .env
    CORS_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS: List[str] = ["*"]

    # Налаштування електронної пошти
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST", None)
    SMTP_PORT: Optional[int] = (
        int(os.getenv("SMTP_PORT", "0")) if os.getenv("SMTP_PORT") else None
    )
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER", None)
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD", None)
    SMTP_SENDER: Optional[str] = os.getenv("SMTP_SENDER", None)

    # Налаштування аудиту дій користувачів
    ENABLE_AUDIT_LOG: bool = os.getenv("ENABLE_AUDIT_LOG", "True").lower() in [
        "true",
        "1",
    ]

    # Налаштування документації API
    ENABLE_SWAGGER: bool = os.getenv("ENABLE_SWAGGER", "True").lower() in ["true", "1"]
    ENABLE_REDOC: bool = os.getenv("ENABLE_REDOC", "True").lower() in ["true", "1"]

    # Налаштування нової системи логування
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    USE_LEGACY_LOGGING: bool = os.getenv("USE_LEGACY_LOGGING", "False").lower() in [
        "true",
        "1",
    ]
    LOG_STORAGE_PRIMARY: str = os.getenv(
        "LOG_STORAGE_PRIMARY", "database"
    )  # database, file, elastic
    LOG_STORAGE_SECONDARY: Optional[str] = os.getenv("LOG_STORAGE_SECONDARY", None)
    LOG_DATABASE_OPERATIONS: bool = os.getenv(
        "LOG_DATABASE_OPERATIONS", "True"
    ).lower() in ["true", "1"]
    LOG_API_REQUESTS: bool = os.getenv("LOG_API_REQUESTS", "True").lower() in [
        "true",
        "1",
    ]
    LOG_SANITIZE_SENSITIVE_DATA: bool = os.getenv(
        "LOG_SANITIZE_SENSITIVE_DATA", "True"
    ).lower() in ["true", "1"]
    LOG_FILE_ROTATION: str = os.getenv("LOG_FILE_ROTATION", "10 MB")
    LOG_FILE_RETENTION: int = int(os.getenv("LOG_FILE_RETENTION", "5"))
    LOG_MAX_FILE_SIZE: int = int(os.getenv("LOG_MAX_FILE_SIZE", "10"))  # MB
    ENVIRONMENT: str = os.getenv(
        "ENVIRONMENT", "development"
    )  # development, production

    @model_validator(mode="after")
    def set_database_urls(self) -> "Settings":
        """
        Set database URLs based on configuration.

        Returns:
            Settings: Self with configured database URLs
        """
        # If SQLite is enabled, override PostgreSQL URLs
        if self.USE_SQLITE:
            self.DATABASE_URL = self.SQLITE_DB_PATH
            self.ASYNC_DATABASE_URL = self.SQLITE_DB_PATH.replace(
                "sqlite:///", "sqlite+aiosqlite:///"
            )
        elif not self.ASYNC_DATABASE_URL and self.DATABASE_URL:
            # Convert SQLAlchemy URL to asyncpg URL for PostgreSQL
            if self.DATABASE_URL.startswith("postgresql://"):
                self.ASYNC_DATABASE_URL = self.DATABASE_URL.replace(
                    "postgresql://", "postgresql+asyncpg://"
                )

        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Створення об'єкту налаштувань
settings = Settings()

# Створення необхідних директорій
os.makedirs(settings.LOGS_DIR, exist_ok=True)
os.makedirs(f"{BASE_DIR}/{settings.UPLOAD_DIR}", exist_ok=True)
