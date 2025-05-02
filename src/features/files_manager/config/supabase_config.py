# Supabase configuration for files_manager module
from src.config.settings import settings

# Використовуємо змінні з налаштувань проекту
SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_KEY = settings.SUPABASE_KEY
SUPABASE_BUCKET = settings.SUPABASE_BUCKET  # Назва bucket в Supabase Storage

# Налаштування дозволу доступу до файлів
DEFAULT_FILE_PERMISSIONS = {"public": True}  # За замовчуванням файли публічні
