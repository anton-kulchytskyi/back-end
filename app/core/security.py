import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.core.logger import logger

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------- PASSWORD UTILS ---------------------- #


def hash_password(password: str) -> str:
    try:
        hashed = pwd_context.hash(password)
        logger.debug("Password hashed successfully")
        return hashed
    except Exception as e:
        logger.error(f"Error hashing password: {str(e)}")
        raise


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        result = pwd_context.verify(plain_password, hashed_password)
        if result:
            logger.debug("Password verification successful")
        else:
            logger.debug("Password verification failed")
        return result
    except Exception as e:
        logger.error(f"Error verifying password: {str(e)}")
        return False


# ---------------------- TOKEN HELPERS ---------------------- #


def _create_token(
    data: dict, secret_key: str, expires_delta: timedelta, token_type: str
) -> str:
    """Internal helper for JWT creation."""
    try:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire, "jti": str(uuid.uuid4())})

        encoded_jwt = jwt.encode(
            to_encode, secret_key, algorithm=settings.auth.ALGORITHM
        )
        logger.debug(
            f"{token_type.capitalize()} token created successfully for subject: {data.get('sub')} "
            f"(jti={to_encode['jti']})"
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating {token_type} token: {str(e)}")
        raise


def _decode_token(token: str, secret_key: str, token_type: str) -> Optional[dict]:
    """Internal helper for JWT decoding."""
    try:
        payload = jwt.decode(token, secret_key, algorithms=[settings.auth.ALGORITHM])
        logger.debug(
            f"{token_type.capitalize()} token decoded successfully for subject: {payload.get('sub')}"
        )
        return payload
    except JWTError as e:
        logger.warning(f"Invalid {token_type} token: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error decoding {token_type} token: {str(e)}")
        return None


# ---------------------- ACCESS TOKEN ---------------------- #


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    try:
        delta = expires_delta or timedelta(
            minutes=settings.auth.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        return _create_token(data, settings.auth.SECRET_KEY, delta, token_type="access")
    except Exception as e:
        logger.error(f"Failed to create access token: {str(e)}")
        raise


def decode_access_token(token: str) -> Optional[dict]:
    return _decode_token(token, settings.auth.SECRET_KEY, token_type="access")


# ---------------------- REFRESH TOKEN ---------------------- #


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    try:
        delta = expires_delta or timedelta(days=settings.auth.REFRESH_TOKEN_EXPIRE_DAYS)
        return _create_token(
            data, settings.auth.REFRESH_SECRET_KEY, delta, token_type="refresh"
        )
    except Exception as e:
        logger.error(f"Failed to create refresh token: {str(e)}")
        raise


def decode_refresh_token(token: str) -> Optional[dict]:
    return _decode_token(token, settings.auth.REFRESH_SECRET_KEY, token_type="refresh")
