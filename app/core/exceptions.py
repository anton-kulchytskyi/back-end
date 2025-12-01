"""Custom exceptions for the application."""

from fastapi import HTTPException, status


# --- Base exception --- #
class BaseAppException(HTTPException):
    """Base exception for all app exceptions."""

    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


# --- Generic HTTP exceptions --- #


class BadRequestException(BaseAppException):
    """Invalid request or business logic violation (400)."""

    def __init__(self, detail: str = "Bad request"):
        super().__init__(status.HTTP_400_BAD_REQUEST, detail)


class UnauthorizedException(BaseAppException):
    """Authentication failed (401)."""

    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail)
        self.headers = {"WWW-Authenticate": "Bearer"}


class PermissionDeniedException(BaseAppException):
    """Permission denied (403)."""

    def __init__(
        self, detail: str = "You don't have permission to perform this action"
    ):
        super().__init__(status.HTTP_403_FORBIDDEN, detail)


class NotFoundException(BaseAppException):
    """Resource not found (404)."""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status.HTTP_404_NOT_FOUND, detail)


class ConflictException(BaseAppException):
    """Resource conflict - duplicate or already exists (409)."""

    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(status.HTTP_409_CONFLICT, detail)


# --- Internal server error --- #


class ServiceException(BaseAppException):
    """Internal server error (500) - use only for unexpected errors."""

    def __init__(self, detail: str = "Internal server error"):
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, detail)


class RedisException(ServiceException):
    """
    Redis operation failed (500).

    Wraps redis-py exceptions to provide consistent error handling
    and decouple application code from Redis library internals.
    """

    def __init__(self, detail: str = "Redis operation failed"):
        super().__init__(detail)
