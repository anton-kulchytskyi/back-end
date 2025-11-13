from app.config.base import BaseConfig


class Auth0Settings(BaseConfig):
    AUTH0_DOMAIN: str = ""
    AUTH0_CLIENT_ID: str = ""
    AUTH0_CLIENT_SECRET: str = ""
    AUTH0_AUDIENCE: str = ""
    AUTH0_ALGORITHMS: str = "RS256"
