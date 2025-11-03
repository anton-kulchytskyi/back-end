from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logger import logger
from app.core.security import hash_password
from app.schemas.user import (
    SignUpRequest,
    UserDetailResponse,
    UsersListResponse,
    UserUpdateRequest,
)
from app.services.user_service import user_service

router = APIRouter()


@router.get("", response_model=UsersListResponse, status_code=status.HTTP_200_OK)
async def get_users(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    db: AsyncSession = Depends(get_db),
):
    try:
        skip = (page - 1) * page_size
        users, total = await user_service.get_all_users(db, skip=skip, limit=page_size)

        total_pages = (total + page_size - 1) // page_size

        return UsersListResponse(
            users=[UserDetailResponse.model_validate(user) for user in users],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users",
        )


@router.get(
    "/{user_id}", response_model=UserDetailResponse, status_code=status.HTTP_200_OK
)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        user = await user_service.get_user_by_id(db, user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id={user_id} not found",
            )

        return UserDetailResponse.model_validate(user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user",
        )


@router.post("", response_model=UserDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: SignUpRequest, db: AsyncSession = Depends(get_db)):
    try:
        # Check if user with email already exists
        existing_user = await user_service.get_user_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email {user_data.email} already exists",
            )

        hashed_password = hash_password(user_data.password)

        user = await user_service.create_user(db, user_data, hashed_password)

        return UserDetailResponse.model_validate(user)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )


@router.put(
    "/{user_id}", response_model=UserDetailResponse, status_code=status.HTTP_200_OK
)
async def update_user(
    user_id: int, user_data: UserUpdateRequest, db: AsyncSession = Depends(get_db)
):
    try:
        user = await user_service.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id={user_id} not found",
            )

        hashed_password = None
        if user_data.password:
            hashed_password = hash_password(user_data.password)

        updated_user = await user_service.update_user(
            db, user, user_data, hashed_password
        )

        return UserDetailResponse.model_validate(updated_user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        user = await user_service.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id={user_id} not found",
            )

        await user_service.delete_user(db, user)

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user",
        )
