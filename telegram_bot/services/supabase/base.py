from supabase import create_client, Client
from telegram_bot.config import settings


class SupabaseBaseService:
    def __init__(self):
        url = getattr(settings, "SUPABASE_API_URL", None) or getattr(
            settings, "SUPABASE_URL", None
        )
        key = getattr(settings, "SUPABASE_API_KEY", None) or getattr(
            settings, "SUPABASE_KEY", None
        )
        if not url or not key:
            raise Exception(
                "SUPABASE_API_URL та SUPABASE_API_KEY повинні бути в .env/config!"
            )
        self.url = url
        self.key = key
        self.client: Client = create_client(self.url, self.key)

    def table_exists(self, table_name: str) -> bool:
        # Supabase не має прямого методу перевірки існування таблиці через REST, але можна спробувати select з limit=1
        try:
            self.client.table(table_name).select("*").limit(1).execute()
            return True  # Якщо не було винятку — таблиця існує
        except Exception:
            return False

    def create_bonuses_table(self):
        # Supabase не дозволяє створювати таблиці через REST API, це треба робити через SQL (PostgREST RPC або SQL API)
        # Тут лише заглушка для прикладу
        raise NotImplementedError(
            "Створення таблиць можливе лише через SQL API Supabase або вручну через консоль."
        )
