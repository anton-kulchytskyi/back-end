from fastapi import HTTPException, status


# --- Base project exceptions --- #
class BaseAppException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


# --- Internal service exception --- #
class ServiceException(BaseAppException):
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


# --- Authentication exceptions --- #
class UnauthorizedException(BaseAppException):
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )
        self.headers = {"WWW-Authenticate": "Bearer"}
