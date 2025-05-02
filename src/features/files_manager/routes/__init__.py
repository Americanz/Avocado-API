"""
Files Manager module routes initialization.
"""

from fastapi import APIRouter

# Import our route modules
# from .routes import router as main_router
# from .file_routes import router as file_router
# from .product_routes import router as product_router
from .table_routes import router as table_router

# Create a parent router for our module
router = APIRouter()

# Include all our routers
# router.include_router(main_router, prefix="")
# router.include_router(file_router, prefix="/storage")
# router.include_router(product_router, prefix="/products")
router.include_router(table_router, prefix="/tables")
