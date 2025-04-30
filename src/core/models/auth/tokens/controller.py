"""
API token controller module.
"""

import secrets
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
import uuid

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.connection import get_db
from src.core.models.auth.tokens.model import Token
from src.core.models.auth.tokens.schemas import (
    TokenCreate,
    TokenUpdate,
    TokenResponse,
    TokenResponseWithoutToken,
)
from src.core.loader_factory.api_factory.controller import APIController


class TokenController(
    APIController[Token, TokenCreate, TokenUpdate, TokenResponseWithoutToken]
):
    """Controller for API tokens."""

    def __init__(self, db: AsyncSession = Depends(get_db)):
        """
        Initialize controller with database session.

        Args:
            db: Database session
        """
        super().__init__(
            model=Token,
            response_schema=TokenResponseWithoutToken,
            db=db,
            search_fields=["name", "description"],
            default_order_by=["-created_at"],
            select_related=["user"],
        )

    def generate_token(self) -> str:
        """
        Generate a secure random API token.

        Returns:
            str: A secure random API token
        """
        return secrets.token_hex(32)  # 64 символов в hex формате

    async def create_token(
        self, token_data: TokenCreate, user_id: str, client_ip: Optional[str] = None
    ) -> TokenResponse:
        """
        Create a new API token for a user.

        Args:
            token_data: Token data
            user_id: User ID
            client_ip: Client IP address

        Returns:
            TokenResponse: Created token
        """
        # Generate new token
        token_value = self.generate_token()

        # Create new token object with additional data
        token_dict = token_data.model_dump()
        token_dict["token"] = token_value
        token_dict["user_id"] = user_id
        token_dict["created_from_ip"] = client_ip

        # Create token using the parent class create method
        token = await self.create(token_dict)

        # Return full token response (with token value)
        return TokenResponse.model_validate(token)

    async def get_token_by_value(self, token_value: str) -> Optional[Token]:
        """
        Get token by value.

        Args:
            token_value: Token value

        Returns:
            Optional[Token]: Token or None if not found
        """
        return await self.get_by_attribute("token", token_value)

    async def get_user_tokens(self, user_id: str) -> List[Token]:
        """
        Get all tokens for a user.

        Args:
            user_id: User ID

        Returns:
            List[Token]: List of tokens
        """
        # Используем метод list с фильтром по user_id
        _, tokens = await self.list(
            page=1,
            page_size=1000,  # большое значение, чтобы получить все токены
            search_filter=(self.model.user_id == user_id),
        )
        return tokens

    async def validate_token(self, token_value: str) -> Optional[Token]:
        """
        Validate token and update last_used_at.

        Args:
            token_value: Token value

        Returns:
            Optional[Token]: Token if valid, None otherwise
        """
        token = await self.get_token_by_value(token_value)
        if not token or not token.is_valid():
            return None

        # Update last_used_at
        token.update_last_used()
        db = await self.get_db_session()
        await db.commit()

        return token

    async def revoke_token(self, token_id: str) -> bool:
        """
        Revoke token (set is_active to False).

        Args:
            token_id: Token ID

        Returns:
            bool: True if token was revoked, False otherwise
        """
        token = await self.get_by_id(token_id)
        if not token:
            return False

        # Revoke token
        token.is_active = False
        db = await self.get_db_session()
        await db.commit()

        return True

    async def get_user_data_from_token(
        self, token_value: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get user data from token.

        Args:
            token_value: Token value

        Returns:
            Optional[Dict[str, Any]]: User data if token is valid, None otherwise
        """
        token = await self.validate_token(token_value)
        if not token:
            return None

        # Get user
        user = token.user
        if not user:
            return None

        # Get user data
        user_data = {
            "user_id": token.user_id,
            "api_token_id": token.id,
            "scopes": token.get_scopes_list(),
            "is_api_token": True,
            "username": getattr(user, "username", None),
            "email": getattr(user, "email", None),
            "is_superuser": getattr(user, "is_superuser", False),
            "disabled": not getattr(user, "is_active", True),
        }

        return user_data


token_controller = TokenController()


__all__ = ["TokenController", "token_controller"]
