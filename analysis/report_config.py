"""
Конфігурація для HTML звітів
"""

# Налаштування генерації звітів
REPORT_CONFIG = {
    # Назва організації для звітів
    "company_name": "Avocado Sales Analytics",
    # Кольорова схема
    "colors": {
        "primary": "#2ecc71",  # Основний зелений
        "secondary": "#27ae60",  # Темно-зелений
        "success": "#27ae60",  # Успіх
        "warning": "#f39c12",  # Попередження
        "danger": "#e74c3c",  # Помилка
        "info": "#3498db",  # Інформація
        "dark": "#2c3e50",  # Темний
        "light": "#ecf0f1",  # Світлий
    },
    # Налаштування графіків
    "charts": {"default_height": 400, "animation_duration": 1000, "responsive": True},
    # Налаштування таблиць
    "tables": {"rows_per_page": 10, "show_search": True, "show_pagination": True},
    # Форматування валют
    "currency": {"symbol": "грн", "decimal_places": 2, "thousands_separator": ","},
    # Налаштування топ-списків
    "limits": {"top_products": 10, "top_clients": 10, "top_spots": 10},
    # Шляхи до файлів
    "paths": {"reports_dir": "reports", "templates_dir": "templates"},
}

# Опис метрик для звітів
METRICS_DESCRIPTIONS = {
    "total_revenue": "Загальний дохід від продажів за весь період",
    "total_transactions": "Загальна кількість транзакцій",
    "avg_check": "Середній розмір чеку",
    "unique_clients": "Кількість унікальних клієнтів",
    "revenue_growth": "Зростання доходу порівняно з попереднім періодом",
    "transaction_growth": "Зростання кількості транзакцій",
}

# Шаблони для рекомендацій
RECOMMENDATION_TEMPLATES = {
    "low_performance_spot": {
        "title": "🏪 Оптимізація роботи точки",
        "description": 'Точка "{name}" показує нижчі від середнього результати. Рекомендується проаналізувати причини та розробити план покращення.',
    },
    "top_product_promotion": {
        "title": "🚀 Промо топ-продуктів",
        "description": 'Продукт "{name}" показує відмінні результати. Варто збільшити рекламну активність для максимізації прибутку.',
    },
    "client_retention": {
        "title": "💝 Утримання клієнтів",
        "description": "Розробити програму лояльності для топ-клієнтів, які генерують {percentage}% від загального доходу.",
    },
    "seasonal_trends": {
        "title": "📅 Сезонні тренди",
        "description": "Виявлено сезонні коливання в продажах. Рекомендується підготувати спеціальні пропозиції для періодів спаду.",
    },
}
