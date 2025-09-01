import os
from typing import List

# Константи для адміністраторів
ADMIN_USER_IDS = os.getenv("TELEGRAM_ADMIN_IDS", "").split(",")


def is_admin(user_id: int) -> bool:
    """Перевіряє, чи є користувач адміністратором"""
    return str(user_id) in ADMIN_USER_IDS


def get_admin_ids() -> List[str]:
    """Повертає список ID адміністраторів"""
    return ADMIN_USER_IDS
