"""
Basic test for database connection.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import text

from src.config import settings


@pytest.mark.asyncio
async def test_db_connection(test_db):
    """
    Test database connection.
    """
    # Перевіряємо, що підключення до бази даних працює
    result = await test_db.execute(text("SELECT 1"))
    assert result.scalar() == 1
    
    # Перевіряємо, що використовується SQLite
    assert "sqlite" in settings.DATABASE_URL
    assert settings.USE_SQLITE == True


@pytest.mark.asyncio
async def test_health_check(test_app):
    """
    Test health check endpoint.
    """
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        response = await client.get(f"{settings.API_PREFIX}/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}