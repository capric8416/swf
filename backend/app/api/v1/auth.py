"""Authentication API endpoints.

TDD Green Phase: Implement auth API endpoints to make tests pass.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_auth_service, get_current_active_user, get_db
from app.core.logging import get_logger
from app.db.models import User
from app.schemas import (
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    RefreshTokenRequest,
    TokenRefreshResponse,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@router.post("/login", response_model=TokenRefreshResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_svc: Annotated[type, Depends(get_auth_service)],
) -> TokenRefreshResponse:
    """Login endpoint to get access and refresh tokens.

    Args:
        form_data: OAuth2 form with username and password.
        db: Database session.
        auth_svc: Auth service module.

    Returns:
        Token response with access and refresh tokens.

    Raises:
        HTTPException: If authentication fails.
    """
    result = await auth_svc.login_user(db, form_data.username, form_data.password)

    if not result:
        logger.warning(f"Login failed for user '{form_data.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"User '{form_data.username}' logged in successfully")

    return TokenRefreshResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"],
        expires_in=3600,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_svc: Annotated[type, Depends(get_auth_service)],
) -> TokenResponse:
    """Refresh access token using refresh token.

    Args:
        request: Refresh token request.
        db: Database session.
        auth_svc: Auth service module.

    Returns:
        New access token response.

    Raises:
        HTTPException: If refresh token is invalid.
    """
    result = await auth_svc.refresh_access_token(db, request.refresh_token)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=result["access_token"],
        token_type=result["token_type"],
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout_endpoint(
    request: LogoutRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_svc: Annotated[type, Depends(get_auth_service)],
) -> LogoutResponse:
    """Logout endpoint to invalidate tokens.

    Args:
        request: Logout request with optional refresh token.
        token: Current access token from Authorization header.
        auth_svc: Auth service module.

    Returns:
        Logout success message.

    Raises:
        HTTPException: If logout fails.
    """
    success = await auth_svc.logout(token, request.refresh_token)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout",
        )

    return LogoutResponse(message="Successfully logged out")


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserResponse:
    """Get current user information.

    Args:
        current_user: Current authenticated user.

    Returns:
        User information.
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        department=current_user.department,
        is_active=current_user.is_active,
        role_id=current_user.role_id,
        role=None,  # TODO: Load role info if needed
    )
