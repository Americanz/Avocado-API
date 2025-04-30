"""
API token model module.
"""

from datetime import datetime
from typing import List

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

from src.core.models.base_model import BaseModel


class Token(BaseModel):
    """
    Model for API tokens.

    These tokens can be used for API authentication as an alternative to OAuth2/JWT authentication.
    """

    __tablename__ = "tokens"

    # Налаштування для універсальних маршрутів
    use_generic_routes = True
    public_routes = False
    search_fields = ["name", "description"]
    default_order_by = ["-created_at"]

    # Поля для зберігання API токенів
    token = Column(
        String(128),
        nullable=False,
        unique=True,
        index=True,
        comment="API токен для автентифікації",
    )

    name = Column(
        String(255),
        nullable=False,
        comment="Назва токену для ідентифікації користувачем",
    )

    description = Column(
        Text,
        nullable=True,
        comment="Опис токену",
    )

    # Зв'язок з користувачем, який створив токен
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="ID користувача, якому належить токен",
    )

    # Права доступу (scopes), збережені як рядок з розділювачем-комою
    scopes = Column(
        String(255),
        nullable=True,
        comment="Права доступу токену (розділені комами)",
    )

    # Активний токен чи ні
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Чи активний токен",
    )

    # Дата та час останнього використання токену
    last_used_at = Column(
        DateTime,
        nullable=True,
        comment="Дата та час останнього використання токену",
    )

    # Дата та час закінчення терміну дії токену (якщо є)
    expires_at = Column(
        DateTime,
        nullable=True,
        comment="Дата та час закінчення терміну дії токену",
    )

    # IP-адреса, з якої був створений токен
    created_from_ip = Column(
        String(45),  # IPv6 addresses can be up to 45 characters
        nullable=True,
        comment="IP-адреса, з якої був створений токен",
    )

    # Отримання відношення до користувача (user буде доступний як властивість)
    user = relationship("User", back_populates="tokens")

    def get_scopes_list(self) -> List[str]:
        """
        Get list of scopes from the scopes string.

        Returns:
            List[str]: List of scopes
        """
        if not self.scopes:
            return []
        return [scope.strip() for scope in self.scopes.split(",")]

    def set_scopes_list(self, scopes: List[str]) -> None:
        """
        Set scopes from a list.

        Args:
            scopes: List of scopes
        """
        if not scopes:
            self.scopes = None
        else:
            self.scopes = ",".join(scopes)

    def is_valid(self) -> bool:
        """
        Check if the token is valid.

        Returns:
            bool: True if token is valid, False otherwise
        """
        # Перевіряємо, чи токен активний
        if not self.is_active:
            return False

        # Перевіряємо, чи не закінчився термін дії
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False

        return True

    def update_last_used(self) -> None:
        """
        Update the last_used_at timestamp.
        """
        self.last_used_at = datetime.utcnow()

    def __repr__(self) -> str:
        """
        String representation of the model.

        Returns:
            str: String representation
        """
        return f"<Token(id={self.id}, name={self.name}, user_id={self.user_id})>"


__all__ = ["Token"]
