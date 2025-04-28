"""
Application constants.
"""


# API константи
API_VERSION = "v1"
API_VERSION_PREFIX = f"/api/{API_VERSION}"  # Изменено с f"/{API_VERSION}" на f"/api/{API_VERSION}"

# Файлові константи
ALLOWED_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "gif", "webp", "svg"]
ALLOWED_DOCUMENT_EXTENSIONS = ["pdf", "doc", "docx", "xls", "xlsx", "csv", "txt"]
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB

# Константи пагінації
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Константи безпеки
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ALGORITHM = "HS256"
PASSWORD_MIN_LENGTH = 8

# Константи бази даних
DB_POOL_SIZE = 5
DB_MAX_OVERFLOW = 10
DB_POOL_TIMEOUT = 30

# Константи валідації
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
PHONE_REGEX = r"^\+?[0-9]{10,15}$"
UUID_REGEX = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"

# Константи для завантаження файлів
UPLOAD_FOLDER = "uploads"
IMAGES_FOLDER = f"{UPLOAD_FOLDER}/images"
DOCUMENTS_FOLDER = f"{UPLOAD_FOLDER}/documents"
TEMP_FOLDER = f"{UPLOAD_FOLDER}/temp"

# Константи для синхронізації
SYNC_BATCH_SIZE = 100
SYNC_TIMEOUT = 60  # seconds

# Типи організаційної структури
ORGANIZATION_TYPES = ["company", "department", "branch", "warehouse"]

# Ролі користувачів
USER_ROLES = [
    "admin",              # Адміністратор системи
    "manager",            # Менеджер
    "sales",              # Продавець
    "warehouse",          # Комірник
    "accountant",         # Бухгалтер
    "user",               # Звичайний користувач
]

# Типи подій журналу
LOG_EVENT_TYPES = [
    "create",             # Створення
    "update",             # Оновлення
    "delete",             # Видалення
    "view",               # Перегляд
    "login",              # Вхід в систему
    "logout",             # Вихід з системи
    "error",              # Помилка
    "warning",            # Попередження
    "info",               # Інформаційне повідомлення
]

# Статуси замовлень
ORDER_STATUSES = [
    "new",                # Нове замовлення
    "processing",         # В обробці
    "completed",          # Виконане
    "cancelled",          # Скасоване
    "pending",            # Очікує на оплату/підтвердження
    "shipped",            # Відправлене
    "delivered",          # Доставлене
]

# Типи оплат
PAYMENT_TYPES = [
    "cash",               # Готівка
    "card",               # Карта
    "bank_transfer",      # Банківський переказ
    "online",             # Онлайн-оплата
    "credit",             # Кредит
]

# Статуси оплат
PAYMENT_STATUSES = [
    "pending",            # Очікує обробки
    "completed",          # Завершена
    "failed",             # Не вдалася
    "refunded",           # Повернена
    "partially_paid",     # Частково оплачена
]
