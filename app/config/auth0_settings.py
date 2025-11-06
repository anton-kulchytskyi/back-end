from app.config.base import BaseConfig


class Auth0Settings(BaseConfig):
    """Auth0 configuration settings"""

    # Auth0 Domain (e.g., dev-xxxxx.us.auth0.com)
    AUTH0_DOMAIN: str = ""

    # Auth0 Client ID
    AUTH0_CLIENT_ID: str = ""

    # Auth0 Client Secret
    AUTH0_CLIENT_SECRET: str = ""

    # Auth0 API Audience (API Identifier)
    AUTH0_AUDIENCE: str = ""

    # Auth0 Algorithms (usually RS256 for Auth0)
    AUTH0_ALGORITHMS: list[str] = ["RS256"]
