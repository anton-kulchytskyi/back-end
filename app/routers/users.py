from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_user, get_user_service
from app.models.user import User
from app.schemas.pagination import PaginationBaseSchema
from app.schemas.user import (
    SignUpRequest,
    UserDetailResponse,
    UsersListResponse,
    UserUpdateRequest,
)
from app.services.users.user_service import UserService

router = APIRouter()


@router.get("", response_model=UsersListResponse)
async def get_users(
    pagination: PaginationBaseSchema = Depends(),
    user_service: UserService = Depends(get_user_service),
):
    """
    Retrieve paginated list of users using unified pagination.
    Query params: ?page=1&limit=10
    """
    return await user_service.get_users_paginated(pagination)


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
):
    """
    Retrieve a single user by ID.
    """
    user = await user_service.get_user_by_id(user_id)
    return UserDetailResponse.model_validate(user)


@router.post("", response_model=UserDetailResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: SignUpRequest,
    user_service: UserService = Depends(get_user_service),
):
    """
    Register a new user.
    """
    user = await user_service.register_user(user_data)
    return UserDetailResponse.model_validate(user)


@router.put("/me", response_model=UserDetailResponse)
async def update_user(
    user_data: UserUpdateRequest,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user),
):
    """
    Update current user's profile. Users can only update their own profile.
    """
    user = await user_service.get_user_by_id(current_user.id)
    updated_user = await user_service.update_user(user, user_data, current_user.id)
    return UserDetailResponse.model_validate(updated_user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user),
):
    """
    Delete current user's profile. Users can only delete their own profile.
    """
    user = await user_service.get_user_by_id(current_user.id)
    await user_service.delete_user(user, current_user.id)
    return None
