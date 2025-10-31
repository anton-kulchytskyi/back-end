from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --- 1. User schema (base) ---
class User(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    is_active: bool = True


# --- 2. SignIn Request model ---
class SignInRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


# --- 3. SignUp Request model ---
class SignUpRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)


# --- 4. UserUpdate Request model ---
class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=100)
    password: str | None = Field(None, min_length=8, max_length=100)


# --- 5. UsersList Response ---
class UsersListResponse(BaseModel):
    users: list["UserDetailResponse"]
    total: int
    page: int = 1
    page_size: int = 10
    total_pages: int


# --- 6. UserDetail Response ---
class UserDetailResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
