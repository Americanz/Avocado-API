"""
Navigation module for Telegram bot.

This module provides centralized navigation management for multi-level menus.
"""

from .menu_manager import MenuManager
from .state import NavigationState

__all__ = ["MenuManager", "NavigationState"]
