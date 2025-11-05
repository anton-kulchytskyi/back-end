from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import SignUpRequest, UserUpdateRequest


class UserService:
    @staticmethod
    async def get_all_users(
        db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> tuple[list[User], int]:
        try:
            # Get total count
            count_query = select(func.count(User.id))
            count_result = await db.execute(count_query)
            total = count_result.scalar_one()

            # Get users with pagination
            query = select(User).offset(skip).limit(limit)
            result = await db.execute(query)
            users = result.scalars().all()

            logger.info(f"Retrieved {len(users)} users (total: {total})")
            return list(users), total

        except Exception as e:
            logger.error(f"Error getting all users: {str(e)}")
            raise

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        try:
            query = select(User).where(User.id == user_id)
            result = await db.execute(query)
            user = result.scalar_one_or_none()

            if user:
                logger.info(f"Retrieved user with id={user_id}")
            else:
                logger.warning(f"User with id={user_id} not found")

            return user

        except Exception as e:
            logger.error(f"Error getting user by id={user_id}: {str(e)}")
            raise

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        try:
            query = select(User).where(User.email == email)
            result = await db.execute(query)
            user = result.scalar_one_or_none()

            if user:
                logger.info(f"Retrieved user with email={email}")
            else:
                logger.warning(f"User with email={email} not found")

            return user

        except Exception as e:
            logger.error(f"Error getting user by email={email}: {str(e)}")
            raise

    @staticmethod
    async def create_user(db: AsyncSession, user_data: SignUpRequest) -> User:
        try:
            hashed_password = hash_password(user_data.password)
            user = User(
                email=user_data.email,
                full_name=user_data.full_name,
                hashed_password=hashed_password,
            )

            db.add(user)
            await db.commit()
            await db.refresh(user)

            logger.info(f"Created user with id={user.id}, email={user.email}")
            return user

        except IntegrityError as e:
            await db.rollback()
            logger.error(f"User with email={user_data.email} already exists")
            raise ValueError(f"User with email {user_data.email} already exists") from e

        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating user: {str(e)}")
            raise

    @staticmethod
    async def update_user(
        db: AsyncSession,
        user: User,
        user_data: UserUpdateRequest,
        hashed_password: str | None = None,
    ) -> User:
        try:
            update_data = user_data.model_dump(exclude_unset=True)

            for field, value in update_data.items():
                if field == "password":
                    continue
                setattr(user, field, value)

            if hashed_password:
                user.hashed_password = hashed_password

            await db.commit()
            await db.refresh(user)

            logger.info(f"Updated user with id={user.id}")
            return user

        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating user with id={user.id}: {str(e)}")
            raise

    @staticmethod
    async def delete_user(db: AsyncSession, user: User) -> bool:
        try:
            await db.delete(user)
            await db.commit()

            logger.info(f"Deleted user with id={user.id}")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting user with id={user.id}: {str(e)}")
            raise

    @staticmethod
    async def authenticate_user(
        db: AsyncSession, email: str, password: str
    ) -> User | None:
        try:
            # Get user by email
            user = await UserService.get_user_by_email(db, email)

            if not user:
                logger.debug(
                    f"Authentication failed: user with email {email} not found"
                )
                return None

            # Verify password
            if not verify_password(password, user.hashed_password):
                logger.debug(
                    f"Authentication failed: invalid password for user {email}"
                )
                return None

            logger.info(f"User authenticated successfully: {email}")
            return user

        except Exception as e:
            logger.error(f"Error authenticating user {email}: {str(e)}")
            return None


user_service = UserService()
