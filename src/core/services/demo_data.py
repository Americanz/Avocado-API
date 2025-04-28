"""
Module for loading demo data.
"""

import json
import logging
import os
import uuid
from pathlib import Path

from sqlalchemy import select, inspect
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.security.password import hash_password
from src.core.models.auth.users import User
from src.core.models.auth.roles import Role  # Використовуємо оновлену модель ролей
from src.core.models.auth.users.controller import UserController


async def create_roles(session: AsyncSession, roles_data: list) -> dict:
    """
    Create roles if they don't exist.

    Args:
        session: Database session
        roles_data: List of role data dictionaries

    Returns:
        Dictionary mapping role names to role objects
    """
    role_objects = {}

    try:
        # Перевіряємо чи існує таблиця roles
        exists = False
        async with session.bind.connect() as conn:
            exists = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).has_table(Role.__tablename__)
            )

        if not exists:
            logging.warning(
                f"Table {Role.__tablename__} does not exist yet, skipping roles creation"
            )
            return role_objects

        # Створюємо ролі або отримуємо існуючі
        for role_data in roles_data:
            # Перевіряємо чи роль вже існує
            result = await session.execute(
                select(Role).where(Role.name == role_data["name"])
            )
            existing_role = result.scalars().first()

            if existing_role:
                logging.info(f"Role '{role_data['name']}' already exists")
                role_objects[role_data["name"]] = existing_role
            else:
                # Створюємо нову роль
                new_role = Role(
                    name=role_data["name"],
                    description=role_data.get("description"),
                    permissions=role_data.get("permissions", {}),
                )
                session.add(new_role)
                await session.flush()  # Для отримання ID без повного commit

                logging.info(f"Created role: {new_role.name}")
                role_objects[role_data["name"]] = new_role

        return role_objects

    except Exception as e:
        logging.error(f"Error creating roles: {e}")
        return role_objects


async def create_admin_user(session: AsyncSession, role_objects: dict) -> None:
    """
    Create admin user if it doesn't exist.

    Args:
        session: Database session
        role_objects: Dictionary mapping role names to role objects
    """
    try:
        # Check if admin already exists
        # Перевіряємо чи існує таблиця users
        exists = False
        async with session.bind.connect() as conn:
            exists = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).has_table(User.__tablename__)
            )

        if not exists:
            logging.warning(
                f"Table {User.__tablename__} does not exist yet, skipping admin user check"
            )
            return

        # Використаємо UserController для пошуку користувача
        user_controller = UserController(session)
        admin = await user_controller.get_by_email("admin@avocado.com")

        if admin:
            logging.info(
                f"Admin user found through controller: {admin.id}, {admin.email}, {admin.username}"
            )

            # Перевіряємо чи має адмін роль admin та призначаємо якщо потрібно
            if "admin" in role_objects and not admin.has_role("admin"):
                admin.set_role(role_objects["admin"])
                logging.info(f"Set admin role to existing admin user")
                await session.commit()

            return
        else:
            logging.info(
                "Admin user not found through controller, will create a new one"
            )

        # Create admin user with UUID
        admin_user = User(
            id=uuid.uuid4(),
            email="admin@avocado.com",
            username="admin",
            first_name="System",
            last_name="Administrator",
            password=hash_password("admin123"),  # Default password
            is_active=True,
            is_superuser=True,
        )

        # Додаємо роль адміністратора, якщо вона існує
        if "admin" in role_objects:
            admin_user.set_role(role_objects["admin"])
            logging.info(f"Set admin role to new admin user")

        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)
        logging.info(f"Admin user created successfully with ID: {admin_user.id}")
    except Exception as e:
        logging.error(f"Error creating admin user: {e}")
        await session.rollback()


async def load_demo_data(session: AsyncSession) -> None:
    """
    Load demo data from JSON files.

    Args:
        session: Database session
    """
    # Перевіряємо чи потрібно завантажувати демо-дані взагалі
    if not settings.LOAD_DEMO_DATA:
        return

    # Перевіряємо чи не існує вже адміністратор - якщо існує, значить
    # базові дані вже були завантажені, і нам не потрібно робити це знову
    admin_exists = False
    try:
        # Перевіряємо чи існує таблиця users
        exists = False
        async with session.bind.connect() as conn:
            exists = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).has_table(User.__tablename__)
            )

        if exists:
            # Перевіряємо чи існує адміністратор
            user_controller = UserController(session)
            admin = await user_controller.get_by_email("admin@avocado.com")
            if admin:
                admin_exists = True
                logging.info("Admin user already exists, skipping demo data loading")
                return
    except Exception as e:
        logging.error(f"Error checking if admin exists: {e}")
        # Продовжуємо виконання, оскільки якщо сталася помилка,
        # можливо таблиця користувачів ще не створена

    # Path to demo data directory
    demo_data_dir = Path("src/core/services/demo_data")

    # Create directory if it doesn't exist
    if not demo_data_dir.exists():
        os.makedirs(demo_data_dir, exist_ok=True)
        logging.info(f"Created demo data directory: {demo_data_dir}")

    # Path to demo data JSON file
    demo_data_path = demo_data_dir / "demo_data.json"

    # If demo data file doesn't exist, create an empty template
    if not demo_data_path.exists():
        demo_data = {
            "roles": [
                {
                    "name": "admin",
                    "description": "Адміністратор системи з повними правами",
                    "permissions": {
                        "user_create": True,
                        "user_read": True,
                        "user_update": True,
                        "user_delete": True,
                        "role_manage": True,
                        "system_settings": True,
                    },
                },
                {
                    "name": "manager",
                    "description": "Менеджер з обмеженими правами адміністрування",
                    "permissions": {
                        "user_read": True,
                        "user_update": True,
                        "sales_manage": True,
                        "reports_view": True,
                        "system_settings": False,
                    },
                },
                {
                    "name": "user",
                    "description": "Звичайний користувач системи",
                    "permissions": {"user_read": True, "profile_edit": True},
                },
            ],
            "users": [
                {
                    "email": "manager@avocado.com",
                    "username": "manager",
                    "full_name": "Store Manager",
                    "password": "manager123",
                    "is_active": True,
                    "is_superuser": False,
                    "role": "manager",  # Змінено з "roles": ["manager"] на "role": "manager"
                }
            ],
            # Add more demo data structures as needed
            # "clients": [],
            # "products": [],
            # "categories": [],
        }

        # Write demo data to file
        with open(demo_data_path, "w", encoding="utf-8") as f:
            json.dump(demo_data, f, indent=4, ensure_ascii=False)

        logging.info(f"Created demo data template at {demo_data_path}")

    # Otherwise, load data from existing file
    else:
        try:
            with open(demo_data_path, "r", encoding="utf-8") as f:
                demo_data = json.load(f)

            # Спочатку створюємо ролі
            role_objects = {}
            if "roles" in demo_data:
                role_objects = await create_roles(session, demo_data["roles"])
                await session.flush()
                logging.info(f"Created {len(role_objects)} roles")

            # Створюємо адміністратора з відповідною роллю
            await create_admin_user(session, role_objects)

            # Process demo data and populate the database
            if "users" in demo_data:
                for user_data in demo_data["users"]:
                    # Check if user already exists
                    result = await session.execute(
                        select(User).where(User.email == user_data["email"])
                    )
                    existing_user = result.scalars().first()

                    if existing_user:
                        # Оновлюємо роль для існуючого користувача
                        role_name = user_data.get("role")
                        if (
                            role_name
                            and role_name in role_objects
                            and not existing_user.has_role(role_name)
                        ):
                            existing_user.set_role(role_objects[role_name])
                            logging.info(
                                f"Set role '{role_name}' to user {existing_user.email}"
                            )
                        continue

                    # Split full_name into first_name and last_name if provided
                    first_name = None
                    last_name = None
                    if "full_name" in user_data and user_data["full_name"]:
                        name_parts = user_data["full_name"].split(maxsplit=1)
                        first_name = name_parts[0] if name_parts else ""
                        last_name = name_parts[1] if len(name_parts) > 1 else ""

                    # Create user with UUID
                    user = User(
                        id=uuid.uuid4(),
                        email=user_data["email"],
                        username=user_data["username"],
                        first_name=user_data.get("first_name", first_name),
                        last_name=user_data.get("last_name", last_name),
                        password=hash_password(user_data["password"]),
                        is_active=user_data["is_active"],
                        is_superuser=user_data["is_superuser"],
                    )
                    session.add(user)
                    await session.flush()  # Для отримання ID без повного commit

                    # Додаємо роль для користувача
                    role_name = user_data.get("role")
                    # Перевіряємо стару структуру (для зворотної сумісності)
                    if not role_name and "roles" in user_data and user_data["roles"]:
                        role_name = user_data["roles"][0]  # Беремо першу роль зі списку

                    if role_name and role_name in role_objects:
                        user.set_role(role_objects[role_name])
                        logging.info(f"Set role '{role_name}' to user {user.email}")

            # Add more data loading logic here for other entities

            await session.commit()
            logging.info("Demo data loaded successfully")

        except Exception as e:
            await session.rollback()
            logging.error(f"Error loading demo data: {e}")
