"""
Script to create products table in Supabase.
Run this to set up the necessary table structure for product imports.
"""

import os
import logging
from supabase import create_client
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Загружаем .env файл
load_dotenv()

def create_products_table():
    """Connect to Supabase and create products table if it doesn't exist"""
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
        
        # SQL запрос для создания таблицы products
        # Примечание: создание таблиц через RPC может быть ограничено в зависимости от настроек безопасности
        create_table_query = """
        CREATE TABLE IF NOT EXISTS products (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ,
            name TEXT NOT NULL,
            sku TEXT NOT NULL UNIQUE,
            price NUMERIC DEFAULT 0,
            quantity INTEGER DEFAULT 0,
            description TEXT,
            category TEXT,
            attributes JSONB,
            image_url TEXT
        );
        
        -- Добавляем индекс для быстрого поиска по SKU
        CREATE INDEX IF NOT EXISTS products_sku_idx ON products (sku);
        """
        
        try:
            # Пытаемся выполнить запрос через RPC функцию exec_sql
            logger.info("Attempting to create products table using RPC...")
            supabase.rpc('exec_sql', {'query': create_table_query}).execute()
            logger.info("Products table created successfully using RPC")
        except Exception as e:
            logger.error(f"Failed to create table using RPC: {str(e)}")
            logger.info("Note: Table creation via RPC may be restricted in Supabase.")
            logger.info("Alternative: Create the table manually through the Supabase dashboard SQL editor.")
            logger.info("SQL to execute in dashboard:")
            logger.info(create_table_query)
            
            # Проверяем, существует ли таблица, пытаясь выбрать данные
            try:
                logger.info("Checking if products table already exists...")
                test_response = supabase.table("products").select("*").limit(1).execute()
                logger.info(f"Products table exists, sample: {test_response.data}")
            except Exception:
                logger.error("Products table does not exist and could not be created automatically.")
                logger.info("Please create the table manually using the SQL query shown above.")
        
    except Exception as e:
        logger.error(f"Error connecting to Supabase: {str(e)}")
        logger.info("Please verify your SUPABASE_API_URL and SUPABASE_API_KEY in the .env file.")
        logger.info("If they are correct, check if your Supabase service is running.")

if __name__ == "__main__":
    create_products_table()