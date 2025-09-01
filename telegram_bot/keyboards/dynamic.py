from typing import List, Dict
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# Приклад функції для отримання кнопок з БД (замість цього буде реальний запит)
def get_keyboard_buttons_from_db(user_id: int) -> List[Dict]:
    # TODO: Реалізувати реальний запит до БД
    # Наприклад, повертаємо список кнопок, які дозволені для цього користувача
    # [{'text': 'Мій баланс', 'enabled': True}, ...]
    return [
        {"text": "Мій баланс", "enabled": True},
        {"text": "Історія бонусів", "enabled": True},
        {"text": "Адмін-панель", "enabled": False},
    ]


def build_dynamic_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    buttons_data = get_keyboard_buttons_from_db(user_id)
    buttons = [
        [KeyboardButton(text=btn["text"])] for btn in buttons_data if btn["enabled"]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
