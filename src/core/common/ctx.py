from contextvars import ContextVar
from typing import Optional, Any, Dict

from starlette.background import BackgroundTasks

# Context variable to store request ID across async context switches
request_id_contextvar: ContextVar[str] = ContextVar('request_id', default='')

# Context for storing request-scoped data
request_context: ContextVar[Dict[str, Any]] = ContextVar('request_context', default={})

CTX_USER_ID: ContextVar[int] = ContextVar("user_id", default=0)
CTX_BG_TASKS: ContextVar[Optional[BackgroundTasks]] = ContextVar("bg_task", default=None)


def get_request_id() -> str:
    """Get current request ID from context variable"""
    return request_id_contextvar.get()


def set_request_id(request_id: str) -> None:
    """Set request ID in context variable"""
    request_id_contextvar.set(request_id)


def get_context_data(key: str, default: Any = None) -> Any:
    """Get data from request context by key"""
    context = request_context.get()
    return context.get(key, default)


def set_context_data(key: str, value: Any) -> None:
    """Set data in request context by key"""
    context = request_context.get().copy()  # Create a copy to avoid modify issues
    context[key] = value
    request_context.set(context)


def clear_context_data() -> None:
    """Clear all request context data"""
    request_context.set({})
