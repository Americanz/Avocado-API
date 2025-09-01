"""
Telegram bot handlers package.
Містить всі обробники повідомлень, команд та callback'ів.
"""

# Експортуємо тільки основні функції реєстрації
from .main import register_all_handlers, register_handlers

__all__ = [
    "register_all_handlers",
    "register_handlers",
]
