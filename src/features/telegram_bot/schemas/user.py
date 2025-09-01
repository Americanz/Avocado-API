"""
Telegram Bot User Service Functions
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session

from ..models import Client


# Service functions for user operations
def get_telegram_user(
    session: Session, telegram_user_id: int
) -> Optional[Dict[str, Any]]:
    """Get telegram user data as dict"""
    client = (
        session.query(Client)
        .filter(Client.telegram_user_id == telegram_user_id)
        .first()
    )

    if client:
        return {
            "user_id": client.telegram_user_id or 0,
            "username": client.telegram_username,
            "first_name": client.telegram_first_name or client.firstname,
            "last_name": client.telegram_last_name or client.lastname,
            "phone": client.phone,
            "is_active": client.is_active,
            "is_blocked": not client.is_telegram_active,
            "language_code": client.telegram_language_code,
            "created_at": client.created_at,
            "updated_at": client.updated_at,
        }
    return None


def create_or_update_telegram_user(
    session: Session,
    telegram_user_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    phone: Optional[str] = None,
    language_code: Optional[str] = None,
) -> Dict[str, Any]:
    """Create or update telegram user"""

    client = (
        session.query(Client)
        .filter(Client.telegram_user_id == telegram_user_id)
        .first()
    )

    if client:
        # Update existing
        if username is not None:
            client.telegram_username = username
        if first_name is not None:
            client.telegram_first_name = first_name
        if last_name is not None:
            client.telegram_last_name = last_name
        if phone is not None:
            client.phone = phone
        if language_code is not None:
            client.telegram_language_code = language_code

        client.telegram_last_activity = datetime.now()
        client.is_telegram_active = True
    else:
        # Create new
        client = Client(
            telegram_user_id=telegram_user_id,
            telegram_username=username,
            telegram_first_name=first_name,
            telegram_last_name=last_name,
            phone=phone,
            telegram_language_code=language_code,
            is_telegram_active=True,
            telegram_joined_at=datetime.now(),
            telegram_last_activity=datetime.now(),
        )
        session.add(client)

    session.commit()
    session.refresh(client)

    return {
        "user_id": client.telegram_user_id or 0,
        "username": client.telegram_username,
        "first_name": client.telegram_first_name or client.firstname,
        "last_name": client.telegram_last_name or client.lastname,
        "phone": client.phone,
        "is_active": client.is_active,
        "is_blocked": not client.is_telegram_active,
        "language_code": client.telegram_language_code,
        "created_at": client.created_at,
        "updated_at": client.updated_at,
    }


def search_telegram_users(session: Session, query: str) -> List[Dict[str, Any]]:
    """Search users by username, name, or phone"""
    clients = (
        session.query(Client)
        .filter(
            (Client.telegram_username.ilike(f"%{query}%"))
            | (Client.telegram_first_name.ilike(f"%{query}%"))
            | (Client.telegram_last_name.ilike(f"%{query}%"))
            | (Client.phone.ilike(f"%{query}%"))
        )
        .limit(10)
        .all()
    )

    return [
        {
            "user_id": client.telegram_user_id or 0,
            "username": client.telegram_username,
            "first_name": client.telegram_first_name or client.firstname,
            "last_name": client.telegram_last_name or client.lastname,
            "phone": client.phone,
            "is_active": client.is_active,
            "is_blocked": not client.is_telegram_active,
            "language_code": client.telegram_language_code,
            "created_at": client.created_at,
            "updated_at": client.updated_at,
        }
        for client in clients
    ]


__all__ = [
    "get_telegram_user",
    "create_or_update_telegram_user",
    "search_telegram_users",
]
