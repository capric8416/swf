"""Authentication service module.

TDD Green Phase: Implement auth service to make tests pass.
"""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.db.models import User


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
        return None

    if not verify_password(password, user.password_hash):
        return None

    # Update last login time
    user.last_login_at = datetime.now(UTC)
    await db.commit()

    return user


async def login_user(db: AsyncSession, username: str, password: str) -> dict[str, str] | None:
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


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> dict[str, str] | None:
    """Refresh an access token using a refresh token.

    Args:
        db: Database session.
        refresh_token: The refresh token to use.

    Returns:
        Dictionary with new access_token and token_type if successful,
        None otherwise.
    """
    try:
        payload = decode_token(refresh_token)
        user_id = int(payload.get("sub", 0))

        if not user_id:
            return None

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            return None

        new_access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username}
        )

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
        }

    except Exception:
        return None
