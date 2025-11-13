"""
Auth0 integration utilities.
Handles Auth0 token verification and user info extraction.
"""

from typing import Optional

import requests
from jose import jwt
from jose.exceptions import JWTError

from app.config import settings
from app.core.logger import logger


class Auth0Error(Exception):
    """Custom exception for Auth0 errors"""

    pass


def get_auth0_public_key(token: str) -> Optional[dict]:
    """
    Get Auth0 public key (JWKS) for token verification.

    Auth0 uses RS256 algorithm with rotating keys.
    We need to fetch the public key from Auth0 JWKS endpoint.

    Args:
        token: JWT token from Auth0

    Returns:
        Public key dict or None if error
    """
    try:
        # Get token header to find key ID (kid)
        unverified_header = jwt.get_unverified_header(token)

        # Fetch JWKS from Auth0
        jwks_url = f"https://{settings.auth0.AUTH0_DOMAIN}/.well-known/jwks.json"
        jwks_response = requests.get(jwks_url, timeout=10)
        jwks_response.raise_for_status()
        jwks = jwks_response.json()

        # Find the key matching token's kid
        for key in jwks.get("keys", []):
            if key.get("kid") == unverified_header.get("kid"):
                logger.debug(f"Found matching public key for kid: {key.get('kid')}")
                return key

        logger.warning(f"No matching key found for kid: {unverified_header.get('kid')}")
        return None

    except requests.RequestException as e:
        logger.error(f"Error fetching JWKS from Auth0: {str(e)}")
        return None
    except JWTError as e:
        logger.error(f"Error parsing token header: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting Auth0 public key: {str(e)}")
        return None


def verify_auth0_token(token: str) -> Optional[dict]:
    """
    Verify Auth0 JWT token and extract payload.

    Args:
        token: JWT token from Auth0

    Returns:
        Token payload if valid, None otherwise

    Raises:
        Auth0Error: If token verification fails
    """
    try:
        # Get public key for verification
        public_key = get_auth0_public_key(token)
        if not public_key:
            logger.warning("Could not retrieve Auth0 public key")
            raise Auth0Error("Could not retrieve Auth0 public key")

        # Verify and decode token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=settings.auth0.AUTH0_ALGORITHMS,
            audience=settings.auth0.AUTH0_AUDIENCE,
            issuer=f"https://{settings.auth0.AUTH0_DOMAIN}/",
        )

        logger.info(
            f"Auth0 token verified successfully for subject: {payload.get('sub')}"
        )
        return payload

    except JWTError as e:
        logger.warning(f"Auth0 token verification failed: {str(e)}")
        raise Auth0Error(f"Invalid Auth0 token: {str(e)}")
    except Exception as e:
        logger.error(f"Error verifying Auth0 token: {str(e)}")
        raise Auth0Error(f"Error verifying Auth0 token: {str(e)}")


def get_email_from_auth0_token(token: str) -> Optional[str]:
    """
    Extract email from Auth0 token.

    Args:
        token: JWT token from Auth0

    Returns:
        User email if found, None otherwise
    """
    try:
        payload = verify_auth0_token(token)

        email = payload.get("email")

        if email:
            logger.debug(f"Extracted email from Auth0 token: {email}")
            return email

        logger.warning("No email found in Auth0 token")
        return None

    except Auth0Error as e:
        logger.warning(f"Could not extract email from token: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error extracting email from Auth0 token: {str(e)}")
        return None
