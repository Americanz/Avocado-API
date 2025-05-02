# """
# Routes for file and product imports
# """
# from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
# from fastapi.responses import JSONResponse
# from typing import Dict, Any, List
# from src.core.security.jwt import get_current_user, JWTPayload
# from ..utils.product_importer import ProductImporter

# router = APIRouter(tags=["product-import"])

# @router.post("/import-products")
# async def import_products(
#     file: UploadFile = File(...),
#     current_user: JWTPayload = Depends(get_current_user)
# ):
#     """
#     Import products from a CSV or Excel file into the products table.

#     The file should contain the following required columns:
#     - name: Product name
#     - sku: Unique product identifier

#     Optional columns:
#     - price: Product price (default 0)
#     - quantity: Product quantity (default 0)
#     - description: Product description
#     - category: Product category
#     - attributes: Product attributes
#     - image_url: URL to product image

#     Returns details about successfully imported products and any errors.
#     """
#     # Проверка типа файла
#     file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''

#     if file_ext not in ['csv', 'xls', 'xlsx']:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Unsupported file format. Please upload a CSV or Excel file."
#         )

#     try:
#         # Читаем содержимое файла
#         file_content = await file.read()

#         # Создаем импортер и обрабатываем файл
#         importer = ProductImporter()
#         success_count, successful_products, failed_products = await importer.import_from_file(
#             file_content=file_content,
#             filename=file.filename
#         )

#         # Формируем ответ
#         return {
#             "success": True,
#             "total_processed": success_count + len(failed_products),
#             "successful_imports": success_count,
#             "successful_products": successful_products[:10],  # Ограничиваем для удобства просмотра
#             "successful_products_count": len(successful_products),
#             "failed_imports": len(failed_products),
#             "failed_products": failed_products[:10],  # Ограничиваем для удобства просмотра
#             "failed_products_count": len(failed_products),
#             "message": f"Successfully imported {success_count} products. Failed to import {len(failed_products)} products."
#         }

#     except ValueError as e:
#         # Обработка ошибок валидации
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )
#     except Exception as e:
#         # Обработка других ошибок
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to import products: {str(e)}"
#         )
