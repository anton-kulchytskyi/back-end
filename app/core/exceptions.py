from fastapi import HTTPException, status


# --- Base project exceptions --- #
class BaseAppException(HTTPException):
    """Base class for all custom project exceptions."""

    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class ServiceException(BaseAppException):
    """Generic internal service exception (500)."""

    def __init__(self, detail: str = "Internal server error"):
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, detail)


# --- Domain-specific exceptions (Users etc.) --- #
class UserNotFoundException(BaseAppException):
    def __init__(self, user_id: int | None = None):
        detail = f"User with id={user_id} not found" if user_id else "User not found"
        super().__init__(status.HTTP_404_NOT_FOUND, detail)


class UserAlreadyExistsException(BaseAppException):
    def __init__(self, email: str):
        super().__init__(
            status.HTTP_409_CONFLICT,
            f"User with email {email} already exists",
        )
