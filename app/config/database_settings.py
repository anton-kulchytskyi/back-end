from pydantic import model_validator

from app.config.base import BaseConfig


class DatabaseSettings(BaseConfig):
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "fastapi_db"
    DATABASE_ECHO: bool = False

    # Direct URL override — Railway/Supabase provide this automatically.
    # If set, individual POSTGRES_* variables are ignored.
    DATABASE_URL: str | None = None

    # Set to True on Railway/cloud (PostgreSQL requires SSL).
    DATABASE_SSL: bool = False

    @model_validator(mode="after")
    def build_database_url(self) -> "DatabaseSettings":
        if self.DATABASE_URL:
            # Railway provides postgresql://, asyncpg needs postgresql+asyncpg://
            url = self.DATABASE_URL
            for prefix in ("postgresql://", "postgres://"):
                if url.startswith(prefix):
                    url = "postgresql+asyncpg://" + url[len(prefix) :]
                    break
            self.DATABASE_URL = url
        else:
            self.DATABASE_URL = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        return self


database_settings = DatabaseSettings()
