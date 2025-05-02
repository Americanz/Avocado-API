"""
Script to list all tables in Supabase database.
Run this to see what tables are available in your Supabase instance.
"""

import sys
import os
import logging
from supabase import create_client
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Загружаем .env файл
load_dotenv()

def list_supabase_tables():
    """Connect to Supabase and list all tables"""
    # Получаем данные для подключения из .env
    supabase_url = os.getenv("SUPABASE_API_URL")
    supabase_key = os.getenv("SUPABASE_API_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("SUPABASE_API_URL or SUPABASE_API_KEY not found in .env file")
        return
    
    logger.info(f"Connecting to Supabase at: {supabase_url}")
    
    try:
        # Создаем клиент Supabase
        supabase = create_client(supabase_url, supabase_key)
        
        # Используем SQL запрос для получения списка таблиц
        # Этот запрос работает с PostgreSQL, который используется в Supabase
        response = supabase.table("products").select("*").limit(1).execute()
        
        # Выводим информацию о таблице products
        logger.info(f"Products table exists: {len(response.data) >= 0}")
        logger.info(f"Products table data sample: {response.data}")
        
        # Получаем список всех таблиц через системные таблицы PostgreSQL
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
        """
        
        # Note: В free-tier Supabase может не быть доступа к выполнению произвольных запросов
        # Если этот запрос не работает, можно использовать альтернативный подход
        try:
            tables_response = supabase.rpc('exec_sql', {'query': tables_query}).execute()
            logger.info(f"Available tables: {tables_response.data}")
        except Exception as e:
            logger.error(f"Could not fetch tables list using RPC: {str(e)}")
            logger.info("Trying to list tables by accessing known tables directly...")
            
            # Пробуем получить данные из нескольких стандартных таблиц
            known_tables = ["products", "files", "users", "categories", "orders", "customers"]
            existing_tables = []
            
            for table in known_tables:
                try:
                    test_response = supabase.table(table).select("*").limit(1).execute()
                    existing_tables.append(table)
                    logger.info(f"Table '{table}' exists, sample: {test_response.data}")
                except Exception:
                    logger.info(f"Table '{table}' does not exist or is not accessible")
            
            logger.info(f"Found these tables: {existing_tables}")
        
    except Exception as e:
        logger.error(f"Error connecting to Supabase: {str(e)}")

if __name__ == "__main__":
    list_supabase_tables()