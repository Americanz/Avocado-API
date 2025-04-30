"""
JWT authentication module.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List

import jwt
from fastapi import Depends, HTTPException, Request, status, Security
from fastapi.security import OAuth2, OAuth2PasswordBearer, SecurityScopes
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel

from src.config import settings
from src.core.models.auth.tokens.controller import token_controller

# OAuth2 scheme for token authentication
API_SCOPES = {
    "admin": "Повний доступ до адміністративних функцій",
    "manager": "Доступ до функцій керування",
    "user": "Базовий доступ користувача",
}


class CustomOAuth2PasswordBearerWithDataField(OAuth2):
    def __init__(self, tokenUrl: str, scopes=None, scheme_name=None):
        scopes = scopes or {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name)

    async def __call__(self, request: Request) -> Optional[str]:
        authorization = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        scheme, param = get_authorization_scheme_param(authorization)
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated: invalid auth scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return param


# Використання модифікованої схеми
oauth2_scheme = CustomOAuth2PasswordBearerWithDataField(
    tokenUrl="/api/v1/users/login", scopes=API_SCOPES
)

# API Key схема авторизації (импортируем из контроллера токенов)
from src.core.models.auth.tokens.auth import api_key_scheme

# Константи для типів доступу
ACCESS_USER = "user"
ACCESS_MANAGER = "manager"
ACCESS_ADMIN = "admin"


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
    scopes: List[str] = None,
) -> str:
    """
    Create JWT access token.

    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time
        scopes: List of permission scopes for the token

    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # Add expiration time and scopes to token data
    to_encode.update({"exp": expire})

    # Add scopes if provided
    if scopes:
        to_encode.update({"scopes": scopes})

    # Encode token
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode JWT access token.

    Args:
        token: JWT token to decode

    Returns:
        Dict[str, Any]: Decoded token data

    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    security_scopes: SecurityScopes = None, token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    Get current user from JWT token and verify scopes if needed.

    Args:
        security_scopes: Required security scopes
        token: JWT token

    Returns:
        Dict[str, Any]: Current user data

    Raises:
        HTTPException: If token is invalid or user doesn't have required permissions
    """
    # Декодуємо токен для отримання даних
    payload = decode_access_token(token)

    # Перевіряємо права доступу, якщо вказані scopes
    if security_scopes and security_scopes.scopes:
        # Перевіряємо, чи користувач є суперкористувачем
        is_superuser = payload.get("is_superuser", False)

        # Якщо користувач є суперкористувачем, він має доступ до всього
        if is_superuser:
            return payload

        # Якщо користувач не є суперкористувачем і потрібен admin доступ
        if "admin" in security_scopes.scopes and not is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions. Superuser access required.",
                headers={
                    "WWW-Authenticate": f'Bearer scope="{security_scopes.scope_str}"'
                },
            )

    return payload


def get_current_active_user(
    current_user: Dict[str, Any] = Security(get_current_user, scopes=[])
) -> Dict[str, Any]:
    """
    Get current active user.

    Args:
        current_user: Current user data

    Returns:
        Dict[str, Any]: Current active user data

    Raises:
        HTTPException: If user is inactive
    """
    if current_user.get("disabled", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


# Додаткові залежності для різних рівнів доступу


def get_current_admin_user(
    current_user: Dict[str, Any] = Security(get_current_user, scopes=["admin"])
) -> Dict[str, Any]:
    """
    Get current active user with admin privileges.

    Args:
        current_user: Current user data

    Returns:
        Dict[str, Any]: Current admin user data

    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.get("is_superuser", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin access required.",
        )
    return current_user


def get_current_manager_user(
    current_user: Dict[str, Any] = Security(
        get_current_user, scopes=["manager", "admin"]
    )
) -> Dict[str, Any]:
    """
    Get current active user with manager privileges.

    Args:
        current_user: Current user data

    Returns:
        Dict[str, Any]: Current manager user data

    Raises:
        HTTPException: If user doesn't have manager or admin role
    """
    # Перевірка прав може бути розширена на основі ролей користувача
    return current_user


def require_auth(
    current_user: Dict[str, Any] = Security(get_current_user, scopes=[])
) -> Dict[str, Any]:
    """
    Simple dependency that just requires authentication.

    Args:
        current_user: Current user data

    Returns:
        Dict[str, Any]: Current user data
    """
    return current_user


# Используем функции из модуля auth.tokens
from src.core.models.auth.tokens.auth import (
    get_current_user_by_api_key,
    get_current_user_universal,
    require_auth_universal,
    get_admin_universal,
)

# Экспортируем функции для использования в других модулях
__all__ = [
    "create_access_token",
    "decode_access_token",
    "get_current_user",
    "get_current_active_user",
    "get_current_admin_user",
    "get_current_manager_user",
    "require_auth",
    "get_current_user_by_api_key",
    "get_current_user_universal",
    "require_auth_universal",
    "get_admin_universal",
    "API_SCOPES",
    "ACCESS_USER",
    "ACCESS_MANAGER",
    "ACCESS_ADMIN",
]
