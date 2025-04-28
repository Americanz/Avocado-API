"""
Protected API routers with authentication requirements.
"""
from fastapi import APIRouter, Depends

from src.core.security.jwt import require_auth, get_current_admin_user, get_current_manager_user

# Створюємо базові роутери з різними рівнями захисту
protected_router = APIRouter(dependencies=[Depends(require_auth)])
admin_router = APIRouter(dependencies=[Depends(get_current_admin_user)])
manager_router = APIRouter(dependencies=[Depends(get_current_manager_user)])

# Функція для створення захищеного роутера з налаштуванням тегів та префіксу
def create_protected_router(
    *, 
    prefix: str = "", 
    tags: list = None, 
    admin_only: bool = False, 
    manager_only: bool = False
) -> APIRouter:
    """
    Create a protected router with specified access level.
    
    Args:
        prefix: URL prefix for the router
        tags: API tags for the router
        admin_only: Whether the router requires admin access
        manager_only: Whether the router requires manager access
        
    Returns:
        Protected APIRouter with appropriate dependencies
    """
    if admin_only:
        return APIRouter(
            prefix=prefix,
            tags=tags,
            dependencies=[Depends(get_current_admin_user)]
        )
    
    if manager_only:
        return APIRouter(
            prefix=prefix,
            tags=tags,
            dependencies=[Depends(get_current_manager_user)]
        )
    
    # Default: basic authentication required
    return APIRouter(
        prefix=prefix,
        tags=tags,
        dependencies=[Depends(require_auth)]
    )