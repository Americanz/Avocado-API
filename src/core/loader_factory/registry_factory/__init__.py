# src/core/loader/module_registry/__init__.py
"""
Module Registry - модуль для реєстрації та завантаження модулів.

Цей модуль забезпечує централізоване управління модулями
та їх завантаження для всього додатку.
"""

from .config import BASE_MODULES, FEATURE_MODULES, ALL_MODULES, REGISTERED_MODULES
from .loader import (
    get_base_modules,
    get_all_registered_modules,
    load_module_routes,
    register_models_from_modules,
    setup_app_modules,
)
from .registry import (
    register_all_models,
    get_model_by_name,
    get_all_models,
)

__all__ = [
    "BASE_MODULES",
    "FEATURE_MODULES",
    "ALL_MODULES",
    "REGISTERED_MODULES",
    "get_base_modules",
    "get_all_registered_modules",
    "load_module_routes",
    "register_models_from_modules",
    "setup_app_modules",
    "register_all_models",
    "get_model_by_name",
    "get_all_models",
]
