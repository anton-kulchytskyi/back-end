from pydantic import model_validator

from app.config.base import BaseConfig


class RedisSettings(BaseConfig):
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Direct URL override — Railway/Upstash provide this automatically.
    # If set, individual REDIS_* variables are ignored.
    REDIS_URL: str | None = None

    @model_validator(mode="after")
    def build_redis_url(self) -> "RedisSettings":
        if not self.REDIS_URL:
            self.REDIS_URL = (
                f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
            )
        return self
