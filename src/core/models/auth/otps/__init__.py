"""
Модуль для роботи з одноразовими паролями (OTP).
"""

from .model import OTP
from .schemas import OTPCreate, OTPUpdate, OTPResponse

# Експортуємо класи, які потрібні для автореєстрації моделей
__all__ = ["OTP", "OTPCreate", "OTPUpdate", "OTPResponse"]

# Спробуємо імпортувати router, але обробляємо можливу помилку
try:
    from .routes import router
    __all__.append("router")
except ImportError:
    print("Router import failed, router not available.")
