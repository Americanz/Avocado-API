from aiogram.dispatcher.middlewares.base import BaseMiddleware
from typing import Callable, Awaitable, Dict, Any
from aiogram import types


class DBSessionMiddleware(BaseMiddleware):
    async def __call__(
        self, handler: Callable, event: types.Message, data: Dict[str, Any]
    ) -> Awaitable:
        # TODO: тут підключення до БД через окремий сервіс/фабрику, а не get_async_session
        # Наприклад:
        # from telegram_bot.services.db import get_session
        # async with get_session() as session:
        #     data["db"] = session
        #     return await handler(event, data)
        return await handler(event, data)
