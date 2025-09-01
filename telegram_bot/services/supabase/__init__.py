# Ініціалізація пакету supabase для імпортів
from telegram_bot.services.supabase.base import SupabaseBaseService
from telegram_bot.services.supabase.service import SupabaseBonusesService

# Створення єдиного екземпляра сервісу для всього додатку
supabase_bonuses_service = SupabaseBonusesService()
