"""
Конфігурація модулів для автоматичного виявлення та завантаження.
"""

# Базові модулі (завжди включені в міграції та API)
BASE_MODULES = [
    "src.core.models.auth.users",
    "src.core.models.auth.roles",
    "src.core.models.auth.otps",
    "src.core.models.auth.tokens",
    "src.core.models.logging",
]

# Додаткові модулі, які використовуються в проекті
FEATURE_MODULES = [
    # "src.features.clients",
    # "src.features.catalog.product",
    # "src.features.catalog.price",
    # "src.features.catalog.category",
    # "src.features.checkbox.reports",
    # "src.features.checkbox.product_sale",
    # "src.features.files_manager",  # Додаємо новий модуль для роботи з Supabase
    # Додайте інші модулі
    #  "src.features.telegram_bot",
]

# Додаткові модулі, які мають інші назви файлів (не model.py)
ADDITIONAL_MODEL_MODULES = [
    "src.features.telegram_bot.models",
]

# Папки, в яких шукати моделі (відносно кореня проекту)
MODEL_SEARCH_PATHS = [
    "src/core/models",
    "src/features",
    # Додайте інші шляхи
]

# Всі активні модулі (об'єднання базових і додаткових)
ALL_MODULES = BASE_MODULES + FEATURE_MODULES + ADDITIONAL_MODEL_MODULES

# Словник зареєстрованих модулів з відповідними API префіксами
# Формат: "module_path": "/api_prefix"
REGISTERED_MODULES = {}


def _initialize_registered_modules() -> None:
    """
    Ініціалізує словник зареєстрованих модулів з відповідними API префіксами.
    """
    global REGISTERED_MODULES

    # Заповнюємо словник базовими модулями
    for module in BASE_MODULES:
        segments = module.split(".")
        prefix = f"/{segments[-1]}"
        REGISTERED_MODULES[module] = prefix

    # Заповнюємо словник функціональними модулями
    for module in FEATURE_MODULES:
        segments = module.split(".")
        if len(segments) >= 3:
            feature_category = segments[-2] if len(segments) > 3 else ""
            feature_name = segments[-1]
            prefix = (
                f"/{feature_category}/{feature_name}"
                if feature_category
                else f"/{feature_name}"
            )
        else:
            prefix = f"/{segments[-1]}"
        REGISTERED_MODULES[module] = prefix


# Ініціалізуємо словник при імпорті модуля
_initialize_registered_modules()
