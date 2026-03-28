"""FastAPI dependencies for the application.

TDD Green Phase: Implement dependencies to make tests pass.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import AsyncSessionLocal

# Security scheme for JWT token
security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncSession:
    """Get database session dependency."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


class CommonQueryParams:
    """Common query parameters for list endpoints."""

    def __init__(self, skip: int = 0, limit: int = 100):
        self.skip = skip
        self.limit = limit


# Type alias for common parameters
CommonParams = Annotated[CommonQueryParams, Depends()]


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Get current user from JWT token.

    This is a placeholder implementation. In production, this would:
    1. Decode the JWT token
    2. Validate the token signature and expiration
    3. Fetch the user from the database
    4. Return the user object
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Placeholder: return a mock user
    # In production, decode JWT and fetch user from database
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "role": "admin",
        "permissions": ["*"],
    }


async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get current active user.

    Checks if the user is active (not disabled).
    """
    # Placeholder: check if user is active
    # In production, check user.is_active flag
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    return current_user


def require_permission(required_permission: str):
    """Create a dependency that requires a specific permission.

    Usage:
        @app.get("/admin-only")
        async def admin_endpoint(
            user: dict = Depends(require_permission("admin"))
        ):
            return {"message": "Admin access granted"}
    """

    async def check_permission(
        current_user: dict = Depends(get_current_active_user),
    ) -> dict:
        """Check if user has required permission."""
        user_permissions = current_user.get("permissions", [])

        # Super admin has all permissions
        if "*" in user_permissions:
            return current_user

        # Check specific permission
        if required_permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {required_permission}",
            )

        return current_user

    return check_permission


# Type aliases for common dependencies
CurrentUser = Annotated[dict, Depends(get_current_user)]
CurrentActiveUser = Annotated[dict, Depends(get_current_active_user)]
DBSession = Annotated[AsyncSession, Depends(get_db)]
