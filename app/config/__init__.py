from app.config.app_settings import AppSettings
from app.config.auth0_settings import Auth0Settings
from app.config.auth_settings import AuthSettings
from app.config.database_settings import DatabaseSettings
from app.config.redis_settings import RedisSettings


class Settings:
    def __init__(self):
        self.app = AppSettings()
        self.auth0 = Auth0Settings()
        self.auth = AuthSettings()
        self.database = DatabaseSettings()
        self.redis = RedisSettings()


settings = Settings()
