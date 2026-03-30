"""Users API endpoints.

TDD Green Phase: Implement users API endpoints to make tests pass.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    Permissions,
    can_modify_user,
    get_current_user,
    get_db,
    is_admin,
    require_admin_permission,
)
from app.core.security import get_password_hash
from app.db.models import User
from app.schemas import (
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.services.auth_service import get_user_by_id

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
async def get_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 100,
) -> list[UserResponse]:
    """Get list of users.

    Args:
        db: Database session.
        current_user: Current authenticated user.
        skip: Number of users to skip.
        limit: Maximum number of users to return.

    Returns:
        List of users.
    """
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            department=user.department,
            is_active=user.is_active,
            role_id=user.role_id,
            role=None,
        )
        for user in users
    ]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin_permission)],
) -> UserResponse:
    """Create a new user.

    Args:
        user_data: User creation data.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        Created user.

    Raises:
        HTTPException: If username or email already exists.
    """
    # Check if username already exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    # Create new user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        department=user_data.department,
        is_active=True,
        role_id=user_data.role_id,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        department=new_user.department,
        is_active=new_user.is_active,
        role_id=new_user.role_id,
        role=None,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """Get user by ID.

    Args:
        user_id: User ID.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        User.

    Raises:
        HTTPException: If user not found.
    """
    user = await get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        department=user.department,
        is_active=user.is_active,
        role_id=user.role_id,
        role=None,
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """Update user.

    Args:
        user_id: User ID.
        user_data: User update data.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        Updated user.

    Raises:
        HTTPException: If user not found or permission denied.
    """
    # Load current user's role to check permissions
    from app.db.models import Role

    result = await db.execute(select(Role).where(Role.id == current_user.role_id))
    current_user_role = result.scalar_one_or_none()
    current_user_permissions = current_user_role.permissions if current_user_role else []
    is_current_user_admin = Permissions.ALL in current_user_permissions or Permissions.ADMIN in current_user_permissions

    # Check permission - admin can update any user, regular users can only update themselves
    if not is_current_user_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: cannot modify other users",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update fields
    if user_data.email is not None:
        user.email = user_data.email
    if user_data.department is not None:
        user.department = user_data.department

    # Only admin can update is_active and role_id
    if user_data.is_active is not None:
        if not is_current_user_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: only admin can change active status",
            )
        user.is_active = user_data.is_active

    if user_data.role_id is not None:
        if not is_current_user_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: only admin can change role",
            )
        user.role_id = user_data.role_id

    await db.commit()
    await db.refresh(user)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        department=user.department,
        is_active=user.is_active,
        role_id=user.role_id,
        role=None,
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin_permission)],
) -> None:
    """Delete user.

    Args:
        user_id: User ID.
        db: Database session.
        current_user: Current authenticated user (must be admin).

    Raises:
        HTTPException: If user not found or permission denied.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent admin from deleting themselves
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    await db.delete(user)
    await db.commit()
