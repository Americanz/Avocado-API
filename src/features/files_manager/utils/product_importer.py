"""
Utility module for importing products data from files to Supabase.
Supports CSV and Excel formats.
"""

import pandas as pd
import io
from typing import List, Dict, Any, Optional, Tuple
import logging
from supabase import create_client
from ..config.supabase_config import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)

# Название таблицы товаров в Supabase
PRODUCTS_TABLE = "products"

class ProductImporter:
    """Class for importing products from files to Supabase"""
    
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
    async def import_from_file(self, file_content: bytes, filename: str) -> Tuple[int, List[str], List[str]]:
        """
        Import products from file (CSV or Excel)
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            
        Returns:
            Tuple containing (number of successfully imported products, 
                             list of successful product names, 
                             list of failed product names with errors)
        """
        try:
            # Определяем формат файла по расширению
            file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
            
            # Создаем буфер из байтов файла
            file_buffer = io.BytesIO(file_content)
            
            # Загружаем данные из файла в DataFrame
            if file_ext == 'csv':
                df = pd.read_csv(file_buffer)
            elif file_ext in ['xls', 'xlsx']:
                df = pd.read_excel(file_buffer)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}. Supported formats: csv, xls, xlsx")
            
            # Проверяем наличие необходимых колонок
            required_columns = ['name', 'sku']  # Минимальный набор обязательных полей
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
            
            # Подготавливаем данные для вставки
            # Преобразуем DataFrame в список словарей
            products_data = df.replace({pd.NA: None}).to_dict('records')
            
            # Чистим данные и приводим к нужному формату
            cleaned_products = self._clean_product_data(products_data)
            
            # Импортируем данные в Supabase
            return await self._import_to_supabase(cleaned_products)
            
        except Exception as e:
            logger.error(f"Error importing products: {str(e)}")
            raise
    
    def _clean_product_data(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean and normalize product data before import
        
        Args:
            products: List of product dictionaries
            
        Returns:
            Cleaned list of product dictionaries
        """
        cleaned_products = []
        
        for product in products:
            # Удаляем пустые значения и преобразуем имена полей
            cleaned_product = {}
            
            for key, value in product.items():
                # Приводим ключи к единому формату (snake_case)
                clean_key = key.lower().strip().replace(' ', '_')
                
                # Только если значение не None
                if value is not None:
                    cleaned_product[clean_key] = value
            
            # Проверяем наличие обязательных полей
            if 'name' in cleaned_product and 'sku' in cleaned_product:
                # Стандартные значения для отсутствующих полей
                if 'price' not in cleaned_product:
                    cleaned_product['price'] = 0
                if 'quantity' not in cleaned_product:
                    cleaned_product['quantity'] = 0
                
                cleaned_products.append(cleaned_product)
        
        return cleaned_products
    
    async def _import_to_supabase(self, products: List[Dict[str, Any]]) -> Tuple[int, List[str], List[str]]:
        """
        Import products to Supabase
        
        Args:
            products: List of product dictionaries
            
        Returns:
            Tuple containing (number of successfully imported products, 
                             list of successful product names, 
                             list of failed product names with errors)
        """
        successful_imports = []
        failed_imports = []
        
        for product in products:
            try:
                # Проверяем, существует ли товар с таким SKU
                response = self.supabase.table(PRODUCTS_TABLE) \
                    .select("id") \
                    .eq("sku", product['sku']) \
                    .execute()
                
                if response.data and len(response.data) > 0:
                    # Обновляем существующий товар
                    product_id = response.data[0]['id']
                    self.supabase.table(PRODUCTS_TABLE) \
                        .update(product) \
                        .eq("id", product_id) \
                        .execute()
                else:
                    # Создаем новый товар
                    self.supabase.table(PRODUCTS_TABLE) \
                        .insert(product) \
                        .execute()
                
                successful_imports.append(product['name'])
                
            except Exception as e:
                logger.error(f"Error importing product {product.get('name', product.get('sku', 'unknown'))}: {str(e)}")
                failed_imports.append(f"{product.get('name', product.get('sku', 'unknown'))}: {str(e)}")
        
        return len(successful_imports), successful_imports, failed_imports