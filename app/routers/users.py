from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.user import (
    SignUpRequest,
    UserDetailResponse,
    UsersListResponse,
    UserUpdateRequest,
)
from app.services.deps import get_user_service
from app.services.user_service import UserService

router = APIRouter()


@router.get("", response_model=UsersListResponse)
async def get_users(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
):
    """
    Retrieve a paginated list of all users.
    """
    skip = (page - 1) * page_size
    users, total = await service.get_all_users(db, skip, page_size)
    total_pages = (total + page_size - 1) // page_size

    return UsersListResponse(
        users=[UserDetailResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
):
    """
    Retrieve a single user by ID.
    """
    user = await service.get_user_by_id(db, user_id)
    return UserDetailResponse.model_validate(user)


@router.post("", response_model=UserDetailResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: SignUpRequest,
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
):
    """
    Register a new user.
    """
    user = await service.register_user(db, user_data)
    return UserDetailResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserDetailResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
):
    """
    Update user info.
    """
    user = await service.get_user_by_id(db, user_id)
    updated_user = await service.update_user(db, user, user_data)
    return UserDetailResponse.model_validate(updated_user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
):
    """
    Delete user by ID.
    """
    user = await service.get_user_by_id(db, user_id)
    await service.delete_user(db, user)
    return None
