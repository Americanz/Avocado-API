# src/core/loader/api_factory/__init__.py
"""
API Factory - модуль для автоматичного створення API маршрутів.

Цей модуль надає інструменти для автоматичного створення RESTful API маршрутів
на основі моделей SQLAlchemy та їх схем.
"""

from .controller import APIController, create_controller
from .routes import create_api_router
from .discovery import discover_and_create_generic_routes

__all__ = [
    "APIController",
    "create_controller",
    "create_api_router",
    "discover_and_create_generic_routes",
]
