"""
Company model for organization management.
"""

from sqlalchemy import  Column, String, Text


from src.core.models.base_model import BaseModel


class Company(BaseModel):
    """Company model for organization."""

    __tablename__ = "companies"

    # Включаємо автоматичну генерацію CRUD API
    use_generic_routes = True
    auth_dependency = True  # Всі маршрути будуть захищені


    # Налаштування для GenericController
    search_fields = ["name", "description", "email", "phone"]
    default_order_by = ["name"]

    name = Column(String, nullable=False)
    legal_name = Column(String, nullable=True)
    tax_id = Column(String, nullable=True)
    registration_number = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    description = Column(Text, nullable=True)


    def __repr__(self) -> str:
        return f"<Company {self.name}>"


__all__ = ["Company"]
