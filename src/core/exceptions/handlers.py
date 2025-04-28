"""
Exception handlers for the application.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from src.core.exceptions.exceptions import (
    ApplicationError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DatabaseError,
    NotFoundException,
    ValidationError,
)


def add_exception_handlers(app: FastAPI) -> None:
    """
    Add exception handlers to the FastAPI application.

    Args:
        app: FastAPI application
    """

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """
        Handle validation errors from FastAPI.
        """
        # Получаем детали ошибки
        details = exc.errors()

        # Заменяем байтовые строки на обычные строки для корректной сериализации
        for detail in details:
            if "input" in detail and isinstance(detail["input"], bytes):
                try:
                    # Пытаемся декодировать байтовые данные как UTF-8
                    detail["input"] = detail["input"].decode("utf-8")
                except UnicodeDecodeError:
                    # Если не удаётся декодировать, просто преобразуем в строку
                    detail["input"] = str(detail["input"])

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "status": "error",
                "message": "Validation error",
                "detail": details,
            },
        )

    @app.exception_handler(ValidationError)
    async def custom_validation_exception_handler(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        """
        Handle custom validation errors.
        """
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "status": "error",
                "message": str(exc),
                "detail": exc.detail if hasattr(exc, "detail") else None,
            },
        )

    @app.exception_handler(NotFoundException)
    async def not_found_exception_handler(
        request: Request, exc: NotFoundException
    ) -> JSONResponse:
        """
        Handle not found errors.
        """
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "status": "error",
                "message": str(exc),
                "detail": exc.detail if hasattr(exc, "detail") else None,
            },
        )

    @app.exception_handler(ConflictError)
    async def conflict_exception_handler(
        request: Request, exc: ConflictError
    ) -> JSONResponse:
        """
        Handle conflict errors.
        """
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "status": "error",
                "message": str(exc),
                "detail": exc.detail if hasattr(exc, "detail") else None,
            },
        )

    @app.exception_handler(AuthenticationError)
    async def authentication_exception_handler(
        request: Request, exc: AuthenticationError
    ) -> JSONResponse:
        """
        Handle authentication errors.
        """
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "status": "error",
                "message": str(exc),
                "detail": exc.detail if hasattr(exc, "detail") else None,
            },
        )

    @app.exception_handler(AuthorizationError)
    async def authorization_exception_handler(
        request: Request, exc: AuthorizationError
    ) -> JSONResponse:
        """
        Handle authorization errors.
        """
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "status": "error",
                "message": str(exc),
                "detail": exc.detail if hasattr(exc, "detail") else None,
            },
        )

    @app.exception_handler(DatabaseError)
    async def database_exception_handler(
        request: Request, exc: DatabaseError
    ) -> JSONResponse:
        """
        Handle database errors.
        """
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "Database error",
                "detail": str(exc),
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(
        request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        """
        Handle SQLAlchemy errors.
        """
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "Database error",
                "detail": str(exc),
            },
        )

    @app.exception_handler(ApplicationError)
    async def application_exception_handler(
        request: Request, exc: ApplicationError
    ) -> JSONResponse:
        """
        Handle general application errors.
        """
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": str(exc),
                "detail": exc.detail if hasattr(exc, "detail") else None,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Handle all other exceptions.
        """
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "Internal server error",
                "detail": str(exc),
            },
        )
