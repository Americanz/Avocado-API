from sqlalchemy import Column, String, JSON
from sqlalchemy.orm import relationship
from src.core.models.base_model import BaseModel


class Role(BaseModel):
    """Role model."""

    __tablename__ = "roles"

    # Налаштування для generic_routes
    use_generic_routes = True
    search_fields = ["name", "description"]
    default_order_by = ["name"]


    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    permissions = Column(
        JSON, nullable=True
    )  # Використовуємо JSON для зберігання дозволів

    # Зв'язок з користувачами (one-to-many)
    users = relationship("User", back_populates="role")

    def __repr__(self):
        return f"<Role(name={self.name}, description={self.description})>"

    def add_permission(self, permission_name):
        """Додає дозвіл до ролі."""
        if not self.permissions:
            self.permissions = {}
        self.permissions[permission_name] = True

    def remove_permission(self, permission_name):
        """Видаляє дозвіл з ролі."""
        if self.permissions and permission_name in self.permissions:
            del self.permissions[permission_name]

    def has_permission(self, permission_name):
        """Перевіряє наявність дозволу."""
        return (
            self.permissions
            and permission_name in self.permissions
            and self.permissions[permission_name]
        )


__all__ = ["Role"]
