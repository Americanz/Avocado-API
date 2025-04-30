"""
API token authentication module.
"""

from typing import Dict, Any, Optional

from fastapi import Depends, HTTPException, Request, status, Security
from fastapi.security import APIKeyHeader

from src.core.models.auth.tokens.controller import token_controller, TokenController

# API Key схема авторизации
api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user_by_api_key(
    api_key: str = Security(api_key_scheme),
    controller: TokenController = Depends(lambda: token_controller),
) -> Optional[Dict[str, Any]]:
    """
    Get current user from API key.

    Args:
        api_key: API key from X-API-Key header
        controller: API token controller

    Returns:
        Dict[str, Any]: Current user data

    Raises:
        HTTPException: If API key is invalid
    """
    if not api_key:
        return None

    # Получаем данные пользователя из токена
    user_data = controller.get_user_data_from_token(api_key)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return user_data


async def get_current_user_universal(
    request: Request,
    api_user: Optional[Dict[str, Any]] = Depends(get_current_user_by_api_key),
) -> Dict[str, Any]:
    """
    Try to authenticate user either by JWT token or API key.

    Args:
        request: FastAPI request object
        api_user: User authenticated by API key

    Returns:
        Dict[str, Any]: Current user data

    Raises:
        HTTPException: If authentication fails
    """
    # Если пользователь уже аутентифицирован через API ключ
    if api_user:
        return api_user

    # Иначе используем стандартную JWT аутентификацию
    from src.core.security.jwt import get_current_user

    # Перенаправляем запрос на стандартную аутентификацию
    return await get_current_user(request)


def require_auth_universal(
    current_user: Dict[str, Any] = Depends(get_current_user_universal)
) -> Dict[str, Any]:
    """
    Simple dependency that requires authentication via JWT or API key.

    Args:
        current_user: Current user data

    Returns:
        Dict[str, Any]: Current user data
    """
    # Проверяем, не отключен ли пользователь
    if current_user.get("disabled", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_admin_universal(
    current_user: Dict[str, Any] = Depends(get_current_user_universal)
) -> Dict[str, Any]:
    """
    Dependency that requires admin privileges via JWT or API key.

    Args:
        current_user: Current user data

    Returns:
        Dict[str, Any]: Current admin user data

    Raises:
        HTTPException: If user doesn't have admin privileges
    """
    # Проверяем, не отключен ли пользователь
    if current_user.get("disabled", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    # Проверяем права администратора
    is_superuser = current_user.get("is_superuser", False)
    has_admin_scope = "admin" in current_user.get("scopes", [])

    if not (is_superuser or has_admin_scope):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin access required.",
        )

    return current_user


__all__ = [
    "api_key_scheme",
    "get_current_user_by_api_key",
    "get_current_user_universal",
    "require_auth_universal",
    "get_admin_universal",
]
