"""
Утиліта для створення красивих клавіатур з правильним розміщенням кнопок
"""

from typing import List, Dict, Optional
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def build_keyboard(buttons_config: List[Dict], columns: int = 2) -> ReplyKeyboardMarkup:
    """
    Створює клавіатуру з кнопок, розміщуючи їх у вказану кількість колонок

    Args:
        buttons_config: Список кнопок з конфігурації
        columns: Кількість колонок (за замовчуванням 2)

    Returns:
        ReplyKeyboardMarkup з красиво розміщеними кнопками
    """
    # Фільтруємо тільки активні кнопки
    enabled_buttons = [btn for btn in buttons_config if btn.get("enabled", True)]

    if not enabled_buttons:
        return ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True)

    # Групуємо кнопки по рядках
    keyboard_rows = []
    current_row = []

    for btn in enabled_buttons:
        # Спеціальна обробка для кнопок "Назад" - вони завжди на окремому рядку
        if btn["text"].startswith("⬅️"):
            # Якщо є незавершений ряд, додаємо його
            if current_row:
                keyboard_rows.append(current_row)
                current_row = []
            # Кнопка "Назад" на окремому рядку
            keyboard_rows.append([KeyboardButton(text=btn["text"])])
            continue

        # Додаємо кнопку до поточного ряду
        current_row.append(KeyboardButton(text=btn["text"]))

        # Якщо ряд заповнений, починаємо новий
        if len(current_row) >= columns:
            keyboard_rows.append(current_row)
            current_row = []

    # Додаємо останній ряд, якщо він не порожній
    if current_row:
        keyboard_rows.append(current_row)

    return ReplyKeyboardMarkup(keyboard=keyboard_rows, resize_keyboard=True)


def build_main_keyboard(
    main_buttons: List[Dict],
    admin_buttons: List[Dict] = None,
    is_admin: bool = False,
    user_phone: Optional[str] = None,
) -> ReplyKeyboardMarkup:
    """
    Створює основну клавіатуру з main кнопками і опціонально admin кнопками

    Args:
        main_buttons: Основні кнопки
        admin_buttons: Адмін кнопки (опціонально)
        is_admin: Чи є користувач адміном
        user_phone: Номер телефону користувача (якщо є, приховуємо кнопку "Поділитись номером")

    Returns:
        ReplyKeyboardMarkup з правильно розміщеними кнопками
    """
    # Фільтруємо main кнопки
    filtered_main_buttons = []
    for btn in main_buttons:
        # Приховуємо кнопку "Поділитись номером" якщо телефон вже є
        if btn["handler"] == "share_phone" and user_phone:
            continue
        filtered_main_buttons.append(btn)

    all_buttons = filtered_main_buttons.copy()

    # Додаємо адмін кнопки, якщо користувач адмін
    if is_admin and admin_buttons:
        # Фільтруємо адмін кнопки, виключаючи навігаційні
        admin_main_buttons = [
            btn
            for btn in admin_buttons
            if btn.get("enabled", True)
            and not btn.get("silent", False)
            and btn["handler"] in ["admin_panel"]  # Тільки головна адмін кнопка
        ]
        all_buttons.extend(admin_main_buttons)

    return build_keyboard(all_buttons, columns=2)


def build_admin_keyboard(admin_buttons: List[Dict]) -> ReplyKeyboardMarkup:
    """
    Створює клавіатуру для адмін панелі

    Args:
        admin_buttons: Список адмін кнопок

    Returns:
        ReplyKeyboardMarkup для адмін панелі
    """
    # Фільтруємо адмін кнопки, виключаючи головну адмін-панель
    panel_buttons = [
        btn
        for btn in admin_buttons
        if btn.get("enabled", True) and btn["handler"] not in ["admin_panel"]
    ]

    return build_keyboard(panel_buttons, columns=2)
