import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

from .base import LogStorage


class FileLogStorage(LogStorage):
    """Сховище логів, що зберігає їх у файлах JSON."""

    def __init__(self, log_dir: str = "logs"):
        """
        Ініціалізує сховище файлових логів.

        Args:
            log_dir: Директорія для зберігання файлів логів
        """
        self.log_dir = log_dir
        self._ensure_log_directories()

    async def store_api_log(self, log_data: Dict[str, Any]) -> Optional[str]:
        """
        Зберігає API лог.

        Args:
            log_data: Дані логу

        Returns:
            ID логу (ім'я файлу без розширення)
        """
        log_id = f"api_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{hash(str(log_data))}"
        file_path = os.path.join(self.log_dir, "api", f"{log_id}.json")
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
            return log_id
        except Exception as e:
            print(f"Error saving API log to file: {e}")
            return None

    async def store_user_log(self, log_data: Dict[str, Any]) -> Optional[str]:
        """
        Зберігає лог дій користувача.

        Args:
            log_data: Дані логу

        Returns:
            ID логу (ім'я файлу без розширення)
        """
        log_id = f"user_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{hash(str(log_data))}"
        file_path = os.path.join(self.log_dir, "user", f"{log_id}.json")
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
            return log_id
        except Exception as e:
            print(f"Error saving user log to file: {e}")
            return None

    async def store_system_log(self, log_data: Dict[str, Any]) -> Optional[str]:
        """
        Зберігає системний лог.

        Args:
            log_data: Дані логу

        Returns:
            ID логу (ім'я файлу без розширення)
        """
        # Визначаємо підкаталог залежно від даних логу
        if log_data.get("operation_type"):
            # Якщо це лог бази даних
            subdir = "database"
        else:
            subdir = "system"
            
        log_id = f"{subdir}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{hash(str(log_data))}"
        file_path = os.path.join(self.log_dir, subdir, f"{log_id}.json")
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
            return log_id
        except Exception as e:
            print(f"Error saving system log to file: {e}")
            return None

    def _ensure_log_directories(self):
        """Створює необхідні директорії для логів, якщо вони не існують."""
        subdirs = ["api", "user", "system", "database"]
        
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
        for subdir in subdirs:
            subdir_path = os.path.join(self.log_dir, subdir)
            if not os.path.exists(subdir_path):
                os.makedirs(subdir_path)