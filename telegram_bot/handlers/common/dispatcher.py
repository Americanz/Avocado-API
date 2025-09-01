from typing import Callable, Dict, Any, Awaitable
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

button_handlers: Dict[str, Callable[[Message], Awaitable[Any]]] = {}
callback_handlers: Dict[str, Callable[[CallbackQuery], Awaitable[Any]]] = {}


def register_button_handler(name: str):
    def decorator(func: Callable[[Message], Awaitable[Any]]):
        button_handlers[name] = func
        return func

    return decorator


def register_callback_handler(name: str):
    def decorator(func: Callable[[CallbackQuery], Awaitable[Any]]):
        callback_handlers[name] = func
        return func

    return decorator


async def dispatch_button_handler(name: str, message: Message, state: FSMContext = None):
    handler = button_handlers.get(name)
    if handler:
        # Check if handler expects state parameter
        import inspect
        sig = inspect.signature(handler)
        if 'state' in sig.parameters:
            if state is None:
                # Create FSMContext if not provided (for compatibility)
                from aiogram.fsm.storage.memory import MemoryStorage
                from aiogram.fsm.storage.base import StorageKey
                
                # Use memory storage as fallback
                storage = MemoryStorage()
                key = StorageKey(bot_id=message.bot.id, chat_id=message.chat.id, user_id=message.from_user.id)
                state = FSMContext(storage=storage, key=key)
            
            return await handler(message, state)
        else:
            return await handler(message)
    else:
        raise ValueError(f"Handler for button '{name}' not found")


async def dispatch_callback_handler(name: str, callback: CallbackQuery, state: FSMContext = None):
    handler = callback_handlers.get(name)
    if handler:
        # Check if handler expects state parameter
        import inspect
        sig = inspect.signature(handler)
        if 'state' in sig.parameters:
            if state is None:
                # Create FSMContext if not provided (for compatibility)
                from aiogram.fsm.storage.memory import MemoryStorage
                from aiogram.fsm.storage.base import StorageKey
                
                # Use memory storage as fallback
                storage = MemoryStorage()
                key = StorageKey(bot_id=callback.message.bot.id, chat_id=callback.message.chat.id, user_id=callback.from_user.id)
                state = FSMContext(storage=storage, key=key)
            
            return await handler(callback, state)
        else:
            return await handler(callback)
    else:
        raise ValueError(f"Callback handler for '{name}' not found")
