"""Authentication API endpoints.

TDD Green Phase: Implement auth API endpoints to make tests pass.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import decode_token
from app.db.models import User
from app.services.auth_service import login_user, refresh_access_token

router = APIRouter(prefix="/auth", tags=["authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str


class TokenRefreshResponse(BaseModel):
    """Token refresh response model."""

    access_token: str
    refresh_token: str
    token_type: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""

    refresh_token: str


class UserResponse(BaseModel):
    """User response model."""

    id: int
    username: str
    email: str
    department: str
    is_active: bool

    class Config:
        """Pydantic config."""

        from_attributes = True


@router.post("/login", response_model=TokenRefreshResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
) -> TokenRefreshResponse:
    """Login endpoint to get access and refresh tokens.

    Args:
        form_data: OAuth2 form with username and password.
        db: Database session.

    Returns:
        Token response with access and refresh tokens.

    Raises:
        HTTPException: If authentication fails.
    """
    result = await login_user(db, form_data.username, form_data.password)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenRefreshResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"],
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Refresh access token using refresh token.

    Args:
        request: Refresh token request.
        db: Database session.

    Returns:
        New access token response.

    Raises:
        HTTPException: If refresh token is invalid.
    """
    result = await refresh_access_token(db, request.refresh_token)

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


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current user from token.

    Args:
        token: JWT access token.
        db: Database session.

    Returns:
        Current user.

    Raises:
        HTTPException: If token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except Exception as err:
        raise credentials_exception from err

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise credentials_exception

    return user


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
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
    )
