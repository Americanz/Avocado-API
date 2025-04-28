"""
Constants for logging functionality
"""

from enum import Enum
import enum


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogDetailType(str, enum.Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    API_CALL = "api_call"
    ERROR = "error"
    STARTUP = "startup"
    SHUTDOWN = "shutdown"
    MAINTENANCE = "maintenance"
    SECURITY = "security"


class LogType(str, enum.Enum):
    API = "api"
    USER = "user"
    SYSTEM = "system"
    DATABASE = "database"
