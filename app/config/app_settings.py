from app.config.base import BaseConfig


class AppSettings(BaseConfig):
    PROJECT_NAME: str = "Qoach"
    ENV: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True
    BACKEND_CORS_ORIGINS: str = ""

    @property
    def get_cors_origins(self) -> list[str]:
        if not self.BACKEND_CORS_ORIGINS:
            return []
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]
