from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logger import logger
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
    """
    Retrieve a list of all users.

    This endpoint provides paginated access to all registered user accounts.

    Args:
        page: The page number to retrieve (starts at 1).
        page_size: The number of items per page (max 100).
        db: Database session dependency.

    Returns:
        UsersListResponse: A list of user details along with pagination metadata.
    """
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
    """
    Retrieve a single user by ID.

    Fetches the detailed information for a specific user ID.

    Args:
        user_id: The ID of the user to retrieve.
        db: Database session dependency.

    Raises:
        HTTPException: 404 Not Found if the user does not exist.

    Returns:
        UserDetailResponse: The detailed information of the requested user.
    """
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
async def register_user(user_data: SignUpRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new user.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        Created user data

    Raises:
        HTTPException:
            - 409 if user with this email already exists
            - 500 if any unexpected error occurs
    """
    try:
        user = await user_service.register_user(db, user_data)
        return UserDetailResponse.model_validate(user)

    except HTTPException:
        raise

    except ValueError as e:
        # Raised when user already exists
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user",
        )


@router.put(
    "/{user_id}", response_model=UserDetailResponse, status_code=status.HTTP_200_OK
)
async def update_user(
    user_id: int, user_data: UserUpdateRequest, db: AsyncSession = Depends(get_db)
):
    """
    Update an existing user's details.

    Allows modification of a user's full name and/or password. The password
    is hashed if provided.

    Args:
        user_id: The ID of the user to update.
        user_data: The update data (full_name and/or password).
        db: Database session dependency.

    Raises:
        HTTPException: 404 Not Found if the user does not exist.

    Returns:
        UserDetailResponse: The updated user details.
    """
    try:
        user = await user_service.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id={user_id} not found",
            )

        updated_user = await user_service.update_user(db, user, user_data)

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
    """
    Delete a user account by ID.

    Removes the user record from the database.

    Args:
        user_id: The ID of the user to delete.
        db: Database session dependency.

    Raises:
        HTTPException: 404 Not Found if the user does not exist.

    Returns:
        None: Returns 204 No Content upon successful deletion.
    """
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
