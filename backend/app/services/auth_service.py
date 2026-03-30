"""Authentication service module.

TDD Green Phase: Implement auth service to make tests pass.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.core.validators import validate_email, validate_password, validate_username
from app.db.models import User
from app.db.redis import TokenBlacklist

logger = get_logger(__name__)


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    """Authenticate a user with username and password.

    Args:
        db: Database session.
        username: The username to authenticate.
        password: The plain text password to verify.

    Returns:
        The User object if authentication succeeds, None otherwise.
    """
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"Authentication failed: user '{username}' not found")
        return None

    if not verify_password(password, user.password_hash):
        logger.warning(f"Authentication failed: invalid password for user '{username}'")
        return None

    # Update last login time (use naive datetime for database compatibility)
    user.last_login_at = datetime.utcnow()
    await db.commit()
    logger.info(f"User '{username}' authenticated successfully")

    return user


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """Get a user by their ID.

    Args:
        db: Database session.
        user_id: The user ID to look up.

    Returns:
        The User object if found, None otherwise.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """Get a user by their username.

    Args:
        db: Database session.
        username: The username to look up.

    Returns:
        The User object if found, None otherwise.
    """
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def validate_token(token: str) -> dict[str, Any] | None:
    """Validate a JWT token and return its payload.

    Args:
        token: The JWT token to validate.

    Returns:
        The decoded token payload if valid, None otherwise.
    """
    try:
        # Check if token is blacklisted
        if await TokenBlacklist.is_blacklisted(token):
            logger.warning("Token validation failed: token is blacklisted")
            return None

        # Decode and validate token
        payload = decode_token(token)
        return payload

    except JWTError as e:
        logger.warning(f"Token validation failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {e}")
        return None


async def login_user(
    db: AsyncSession, username: str, password: str
) -> dict[str, str] | None:
    """Login a user and return tokens.

    Args:
        db: Database session.
        username: The username to login.
        password: The plain text password.

    Returns:
        Dictionary with access_token, refresh_token, and token_type if successful,
        None otherwise.
    """
    user = await authenticate_user(db, username, password)

    if not user:
        return None

    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username}
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


async def refresh_access_token(
    db: AsyncSession, refresh_token: str
) -> dict[str, str] | None:
    """Refresh an access token using a refresh token.

    Args:
        db: Database session.
        refresh_token: The refresh token to use.

    Returns:
        Dictionary with new access_token and token_type if successful,
        None otherwise.
    """
    try:
        # Check if refresh token is blacklisted
        if await TokenBlacklist.is_blacklisted(refresh_token):
            logger.warning("Token refresh failed: refresh token is blacklisted")
            return None

        payload = decode_token(refresh_token)
        user_id = int(payload.get("sub", 0))

        if not user_id:
            logger.warning("Token refresh failed: no subject in token")
            return None

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            logger.warning(f"Token refresh failed: user {user_id} not found or inactive")
            return None

        new_access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username}
        )

        logger.info(f"Access token refreshed for user {user_id}")
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
        }

    except JWTError as e:
        logger.warning(f"Token refresh failed: invalid token - {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {e}")
        return None


async def logout(access_token: str, refresh_token: str | None = None) -> bool:
    """Logout a user by blacklisting their tokens.

    Args:
        access_token: The access token to blacklist.
        refresh_token: Optional refresh token to blacklist.

    Returns:
        True if logout was successful, False otherwise.
    """
    try:
        # Calculate token expiration times for Redis TTL
        access_token_ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        refresh_token_ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

        # Blacklist access token
        access_result = await TokenBlacklist.blacklist_token(access_token, access_token_ttl)

        # Blacklist refresh token if provided
        refresh_result = True
        if refresh_token:
            refresh_result = await TokenBlacklist.blacklist_token(
                refresh_token, refresh_token_ttl
            )

        if access_result and refresh_result:
            logger.info("User logged out successfully")
            return True
        else:
            logger.error("Failed to blacklist tokens during logout")
            return False

    except Exception as e:
        logger.error(f"Unexpected error during logout: {e}")
        return False
