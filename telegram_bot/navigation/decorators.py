"""
Decorator module for registering button handlers.

Provides decorators for easier button handler registration.
"""

import functools
from typing import Callable, Dict, Any

# Global registry for button handlers
_BUTTON_HANDLERS: Dict[str, Callable] = {}


def button_handler(handler_name: str):
    """
    Decorator for registering button handlers.

    Args:
        handler_name: Unique identifier for the handler, matching the 'handler' field in keyboards.json

    Example:
        ```python
        @button_handler("admin_panel")
        async def admin_panel_handler(message, **kwargs):
            # Handler implementation
            pass
        ```
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        # Register the handler
        _BUTTON_HANDLERS[handler_name] = wrapper
        return wrapper

    return decorator


def get_button_handlers() -> Dict[str, Callable]:
    """Get all registered button handlers."""
    return _BUTTON_HANDLERS
