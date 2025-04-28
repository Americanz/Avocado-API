"""
Application exceptions.
"""
import http
from typing import Any, Optional


class ApplicationError(Exception):
    """Base application exception."""

    def __init__(self, message: str, detail: Optional[Any] = None):
        """
        Initialize application exception.

        Args:
            message: Error message
            detail: Optional detailed information
        """
        self.message = message
        self.detail = detail
        super().__init__(message)


class ValidationError(ApplicationError):
    """Validation error exception."""

    pass


class NotFoundException(ApplicationError):
    """Not found exception."""

    pass


class AuthenticationError(ApplicationError):
    """Authentication error exception."""

    pass


class AuthorizationError(ApplicationError):
    """Authorization error exception."""

    pass


class ConflictError(ApplicationError):
    """Conflict error exception."""

    pass


class DatabaseError(ApplicationError):
    """Database error exception."""

    pass


class ExternalServiceError(ApplicationError):
    """External service error exception."""

    pass


class RateLimitError(ApplicationError):
    """Rate limit error exception."""

    pass


class FileError(ApplicationError):
    """File error exception."""

    pass


class HTTPException(Exception):
    def __init__(
            self,
            code: int | str,
            msg: str | None = None
    ) -> None:
        if msg is None:
            msg = http.HTTPStatus(int(code)).phrase
        self.code = code
        self.msg = msg

    def __str__(self) -> str:
        return f"{self.code}: {self.msg}"

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}(code={self.code!r}, msg={self.msg!r})"
