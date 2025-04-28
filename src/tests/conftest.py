"""
Test configuration module.
"""
import os
from typing import AsyncGenerator, Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from src.config import settings
from src.core.database.connection import Base, get_db
from src.main import create_app

# Перевірте, чи знаходимося в режимі тестування
settings.USE_SQLITE = True
settings.ASYNC_DATABASE_URL = settings.TEST_SQLITE_DB_PATH.replace("sqlite:///", "sqlite+aiosqlite:///")
settings.DATABASE_URL = settings.TEST_SQLITE_DB_PATH


# Створення тестових баз даних
test_async_engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

test_engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Створення тестових сесій
TestingAsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_async_engine,
    expire_on_commit=False,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Override get_db dependency for testing.
    
    Yields:
        AsyncSession: Testing database session
    """
    async with TestingAsyncSessionLocal() as session:
        yield session


@pytest.fixture(scope="session")
def test_app() -> Generator[FastAPI, None, None]:
    """
    Create test app with test database.
    
    Yields:
        FastAPI: Test FastAPI application
    """
    # Створення тестового додатку
    app = create_app()
    
    # Створення тестових таблиць
    Base.metadata.create_all(bind=test_engine)
    
    # Переопределение зависимости бази даних
    app.dependency_overrides[get_db] = override_get_db
    
    yield app
    
    # Очищення після тестів
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="session")
def test_client(test_app: FastAPI) -> Generator[TestClient, None, None]:
    """
    Create test client.
    
    Args:
        test_app: Test FastAPI application
    
    Yields:
        TestClient: FastAPI test client
    """
    with TestClient(test_app) as client:
        yield client


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database session for test function.
    
    Yields:
        AsyncSession: Test database session
    """
    # Перед каждым тестом создаем сессию
    async with TestingAsyncSessionLocal() as session:
        yield session
        
        # После каждого теста откатываем изменения
        await session.rollback()