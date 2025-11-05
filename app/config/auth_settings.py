from app.config.base import BaseConfig


class AuthSettings(BaseConfig):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
