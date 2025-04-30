"""
API token routes module.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status, Path
from sqlalchemy import select

from src.core.models.auth.tokens.controller import token_controller, TokenController
from src.core.models.auth.tokens.model import Token
from src.core.models.auth.tokens.schemas import (
    TokenCreate,
    TokenUpdate,
    TokenResponse,
    TokenResponseWithoutToken,
)
from src.core.security.jwt import require_auth, get_admin_universal
from src.core.schemas.responses import Success, SuccessExtra

router = APIRouter(
    tags=["tokens"],
)


@router.post(
    "/",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створити новий API токен",
)
async def create_token(
    token_data: TokenCreate,
    request: Request,
    current_user: dict = Depends(require_auth),
    controller: TokenController = Depends(),
):
    """
    Створення нового API токену для поточного користувача.

    Тільки авторизовані користувачі можуть створювати токени для себе.
    Адміністратори можуть створювати токени для будь-якого користувача.
    """
    # Отримуємо ID користувача - перевіряємо різні можливі ключі
    user_id = None
    if "user_id" in current_user:
        user_id = current_user["user_id"]
    elif "id" in current_user:
        user_id = current_user["id"]
    elif "sub" in current_user:
        user_id = current_user["sub"]
    else:
        # Якщо жоден з ключів не знайдено, викидаємо помилку
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cannot determine user ID from authentication information",
        )

    # Якщо вказано user_id в даних запиту і користувач є адміністратором, використовуємо його
    if token_data.user_id and current_user.get("is_superuser"):
        user_id = token_data.user_id

    # Отримуємо IP клієнта
    client_ip = request.client.host if request.client else None

    # Створюємо токен
    token = await controller.create_token(token_data, user_id, client_ip)

    # Повертаємо відповідь у стандартному форматі
    return Success(data=token)


@router.get(
    "/",
    response_model=List[TokenResponseWithoutToken],
    summary="Отримати список токенів поточного користувача",
)
async def get_user_tokens(
    current_user: dict = Depends(require_auth),
    controller: TokenController = Depends(),
):
    """
    Отримання списку всіх API токенів поточного користувача.

    Тільки авторизовані користувачі можуть отримати свої токени.
    """
    # Отримуємо ID користувача - перевіряємо різні можливі ключі
    user_id = None
    if "user_id" in current_user:
        user_id = current_user["user_id"]
    elif "id" in current_user:
        user_id = current_user["id"]
    elif "sub" in current_user:
        user_id = current_user["sub"]
    else:
        # Якщо жоден з ключів не знайдено, викидаємо помилку
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cannot determine user ID from authentication information",
        )

    # Отримуємо токени користувача з використанням метода list для отримання загальної кількості
    total, tokens = await controller.list(
        page=1,
        page_size=1000,  # використовуємо велике значення, щоб отримати всі токени
        search_filter=(controller.model.user_id == user_id),
    )

    # Повертаємо відповідь у стандартному форматі з пагінацією
    return SuccessExtra(data=tokens, total=total, current=1, size=len(tokens))


@router.get(
    "/{token_id}",
    response_model=TokenResponseWithoutToken,
    summary="Отримати інформацію про токен",
)
async def get_token(
    token_id: str = Path(..., description="ID токену"),
    current_user: dict = Depends(require_auth),
    controller: TokenController = Depends(),
):
    """
    Отримання інформації про конкретний API токен.

    Користувачі можуть отримати інформацію тільки про свої токени.
    Адміністратори можуть отримати інформацію про будь-які токени.
    """
    # Отримуємо ID користувача
    user_id = None
    if "user_id" in current_user:
        user_id = current_user["user_id"]
    elif "id" in current_user:
        user_id = current_user["id"]
    elif "sub" in current_user:
        user_id = current_user["sub"]
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cannot determine user ID from authentication information",
        )

    # Отримуємо токен
    token = await controller.get_by_id(token_id)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found",
        )

    # Перевіряємо права доступу
    if token.user_id != user_id and not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden",
        )

    # Повертаємо токен у стандартному форматі
    return Success(data=token)


@router.put(
    "/{token_id}",
    response_model=TokenResponseWithoutToken,
    summary="Оновити токен",
)
async def update_token(
    token_data: TokenUpdate,
    token_id: str = Path(..., description="ID токену"),
    current_user: dict = Depends(require_auth),
    controller: TokenController = Depends(),
):
    """
    Оновлення інформації про API токен.

    Користувачі можуть оновлювати тільки свої токени.
    Адміністратори можуть оновлювати будь-які токени.
    """
    # Отримуємо ID користувача
    user_id = None
    if "user_id" in current_user:
        user_id = current_user["user_id"]
    elif "id" in current_user:
        user_id = current_user["id"]
    elif "sub" in current_user:
        user_id = current_user["sub"]
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cannot determine user ID from authentication information",
        )

    # Отримуємо токен
    token = await controller.get_by_id(token_id)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found",
        )

    # Перевіряємо права доступу
    if token.user_id != user_id and not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden",
        )

    # Оновлюємо токен
    updated_token = await controller.update(token_id, token_data)
    if not updated_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update token",
        )

    # Повертаємо оновлений токен у стандартному форматі
    return Success(data=updated_token)


@router.delete(
    "/{token_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити токен",
)
async def delete_token(
    token_id: str = Path(..., description="ID токену"),
    current_user: dict = Depends(require_auth),
    controller: TokenController = Depends(),
):
    """
    Видалення токену.

    Користувачі можуть видаляти тільки свої токени.
    Адміністратори можуть видаляти будь-які токени.
    """
    # Отримуємо ID користувача
    user_id = None
    if "user_id" in current_user:
        user_id = current_user["user_id"]
    elif "id" in current_user:
        user_id = current_user["id"]
    elif "sub" in current_user:
        user_id = current_user["sub"]
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cannot determine user ID from authentication information",
        )

    # Отримуємо токен
    token = await controller.get_by_id(token_id)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found",
        )

    # Перевіряємо права доступу
    if token.user_id != user_id and not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden",
        )

    # Видаляємо токен
    success = await controller.delete(token_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete token",
        )

    # Для маршруту DELETE не потрібно повертати тіло відповіді


@router.post(
    "/{token_id}/revoke",
    response_model=TokenResponseWithoutToken,
    summary="Відкликати токен",
)
async def revoke_token(
    token_id: str = Path(..., description="ID токену"),
    current_user: dict = Depends(require_auth),
    controller: TokenController = Depends(),
):
    """
    Відкликання токену (деактивація без видалення).

    Користувачі можуть відкликати тільки свої токени.
    Адміністратори можуть відкликати будь-які токени.
    """
    # Отримуємо ID користувача
    user_id = None
    if "user_id" in current_user:
        user_id = current_user["user_id"]
    elif "id" in current_user:
        user_id = current_user["id"]
    elif "sub" in current_user:
        user_id = current_user["sub"]
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cannot determine user ID from authentication information",
        )

    # Отримуємо токен
    token = await controller.get_by_id(token_id)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found",
        )

    # Перевіряємо права доступу
    if token.user_id != user_id and not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden",
        )

    # Відкликаємо токен
    success = await controller.revoke_token(token_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke token",
        )

    # Повертаємо оновлений токен у стандартному форматі
    token = await controller.get_by_id(token_id)
    return Success(data=token)


# Роут для адміністраторів для перегляду всіх токенів
@router.get(
    "/admin/all",
    response_model=List[TokenResponseWithoutToken],
    summary="[Admin] Отримати список всіх токенів",
)
async def get_all_tokens(
    current_user: dict = Depends(get_admin_universal),
    controller: TokenController = Depends(),
):
    """
    Отримання списку всіх токенів (тільки для адміністраторів).
    """
    # Отримуємо всі токени з бази даних з використанням стандартного методу list
    total, tokens = await controller.list(
        page=1,
        page_size=1000,  # використовуємо велике значення, щоб отримати всі токени
    )

    # Повертаємо список токенів у стандартному форматі з пагінацією
    return SuccessExtra(data=tokens, total=total, current=1, size=len(tokens))
