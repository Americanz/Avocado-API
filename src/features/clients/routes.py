"""
Client routes module.
"""

from fastapi import APIRouter

from src.core.models.loader.generic_routes import create_api_router
from src.core.models.loader.generic_controller import create_controller
from src.core.security.jwt import require_auth
from src.features.clients.model import Client, ClientGroup, ClientContact
from src.features.clients.schemas import (
    ClientCreate,
    ClientUpdate,
    ClientResponse,
    ClientGroupCreate,
    ClientGroupUpdate,
    ClientGroupResponse,
    ClientContactCreate,
    ClientContactUpdate,
    ClientContactResponse,
)

# Створюємо маршрутизатор з універсальними CRUD операціями для клієнтів
router = create_api_router(
    controller=create_controller(Client, ClientResponse),
    create_schema=ClientCreate,
    update_schema=ClientUpdate,
    response_schema=ClientResponse,
    prefix="/clients",
    tags=["clients"],
    auth_dependency=require_auth,
)

# Створюємо маршрутизатор з універсальними CRUD операціями для груп клієнтів
groups_router = create_api_router(
    controller=create_controller(ClientGroup, ClientGroupResponse),
    create_schema=ClientGroupCreate,
    update_schema=ClientGroupUpdate,
    response_schema=ClientGroupResponse,
    prefix="/client-groups",
    tags=["client-groups"],
    auth_dependency=require_auth,
)

# Додаємо маршрутизатор груп клієнтів до основного маршрутизатора
router.include_router(groups_router)

# В майбутньому можна додати більше спеціалізованих маршрутів для роботи з контактами
