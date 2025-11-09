from pydantic import BaseModel


# --- 1. Request model for Auth0 loginl ---
class Auth0LoginRequest(BaseModel):
    token: str


# --- 2. Response model for login endpoints ---
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
