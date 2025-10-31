from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


# --- Base Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: Optional[bool] = True


# --- 1. Request Models (Input) ---


class UserCreate(UserBase):
    password: str


class UserSignIn(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None


# --- 2. Response Models (Output) ---
class UserPublic(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UsersList(BaseModel):
    users: list[UserPublic]
    total: int


# --- 3. Authentication Response ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
