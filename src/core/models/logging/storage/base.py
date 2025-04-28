import abc
from typing import Dict, Any, Optional


class LogStorage(abc.ABC):
    """Абстрактний клас для різних способів зберігання логів"""

    @abc.abstractmethod
    async def store_api_log(self, log_data: Dict[str, Any]) -> Optional[str]:
        """Зберігає API лог і повертає його ID"""
        pass

    @abc.abstractmethod
    async def store_user_log(self, log_data: Dict[str, Any]) -> Optional[str]:
        """Зберігає лог дій користувача"""
        pass

    @abc.abstractmethod
    async def store_system_log(self, log_data: Dict[str, Any]) -> Optional[str]:
        """Зберігає системний лог"""
        pass
