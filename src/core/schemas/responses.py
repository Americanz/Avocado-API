"""
Кастомні відповіді для API з підтримкою дат.
"""

from typing import Any
import json
from datetime import datetime, date
from uuid import UUID
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class JSONEncoder(json.JSONEncoder):
    """Розширений JSON енкодер з підтримкою спеціальних типів."""

    def default(self, obj):
        """Обробка спеціальних типів."""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        # Додаємо підтримку Pydantic моделей
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        return super().default(obj)


class Custom(JSONResponse):
    """Базовий клас для кастомних відповідей."""

    def __init__(
        self,
        code: str | int = "0000",
        status_code: int = 200,
        msg: str = "OK",
        data: Any = None,
        **kwargs,
    ):
        content = {"code": str(code), "msg": msg, "data": data}
        content.update(kwargs)

        # Використовуємо власний JSON encoder для обробки дат та UUID
        content_str = json.dumps(content, cls=JSONEncoder)
        content_dict = json.loads(content_str)

        super().__init__(content=content_dict, status_code=status_code)


class Success(Custom):
    """Успішна відповідь."""

    pass


class Fail(Custom):
    """Відповідь з помилкою."""

    def __init__(
        self,
        code: str | int = "4000",
        msg: str = "OK",
        data: Any = None,
        **kwargs,
    ):
        super().__init__(code=code, msg=msg, data=data, status_code=200, **kwargs)


class SuccessExtra(Custom):
    """Успішна відповідь з додатковими полями для пагінації."""

    def __init__(
        self,
        code: str | int = "0000",
        msg: str = "OK",
        data: Any = None,
        total: int = 0,
        current: int = 1,
        size: int = 20,
        **kwargs,
    ):
        # Додаємо параметри пагінації як окремі поля в контенті, а не в data
        super().__init__(
            code=code,
            msg=msg,
            data=data,
            total=total,
            current=current,
            size=size,
            status_code=200,
            **kwargs,
        )
