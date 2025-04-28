from sqlalchemy import Boolean, Column, String, ForeignKey
from sqlalchemy.orm import relationship
from src.core.models.base_model import BaseModel


class User(BaseModel):
    """User model."""

    __tablename__ = "users"

    # Налаштування для універсальних маршрутів
    use_generic_routes = True  # Вмикаємо універсальні маршрути
    public_routes = False  # Маршрути потребують авторизації
    search_fields = ["email", "username", "first_name", "last_name"]
    default_order_by = ["email"]
    select_related = ["role"]


    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=True, index=True)
    password = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    is_superuser = Column(Boolean, default=False, nullable=False)


    role_id = Column(String(36), ForeignKey("roles.id"), nullable=True)
    role = relationship("Role", back_populates="users")

    def __str__(self):
        return self.username or self.email  # Повертаємо email, якщо username порожній

    @property
    def full_name(self):
        """Повертає повне ім'я користувача."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username or self.email

    def set_role(self, role):
        """Встановлює роль користувачу."""
        self.role = role
        self.role_id = role.id if role else None

    def remove_role(self):
        """Видаляє роль у користувача."""
        self.role = None
        self.role_id = None

    def has_role(self, role_name):
        """Перевіряє, чи має користувач роль з вказаною назвою."""
        return self.role and self.role.name == role_name

    def has_permission(self, permission_name):
        """Перевіряє, чи має користувач конкретний дозвіл через свою роль."""
        if self.is_superuser:
            return True
        return self.role and self.role.has_permission(permission_name)


__all__ = ["User"]
