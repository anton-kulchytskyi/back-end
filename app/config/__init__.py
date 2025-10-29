from app.config.app_settings import AppSettings
from app.config.database_settings import DatabaseSettings
from app.config.redis_settings import RedisSettings


class Settings:
    def __init__(self):
        self.app = AppSettings()
        self.database = DatabaseSettings()
        self.redis = RedisSettings()


settings = Settings()
