"""Pydantic schemas for request/response validation."""

from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    RefreshTokenRequest,
    TokenRefreshResponse,
    TokenResponse,
)
from app.schemas.common import ApiResponse, ErrorResponse
from app.schemas.project import (
    ProjectCreate,
    ProjectInDB,
    ProjectListResponse,
    ProjectMemberCreate,
    ProjectMemberListResponse,
    ProjectMemberResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.schemas.stats import (
    ActivityTrendResponse,
    AIAdoptionResponse,
    BugTrendResponse,
    CodeRankResponse,
    PersonalBugRateResponse,
    PersonalCodeStatsResponse,
    PersonalTokenStatsResponse,
    ProjectStatsResponse,
    TokenTrendResponse,
    TopUserResponse,
)
from app.schemas.user import (
    RoleResponse,
    UserCreate,
    UserInDB,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from app.schemas.sync import (
    SyncTaskCreate,
    SyncTaskResponse,
    SyncTaskListResponse,
)

__all__ = [
    # Common
    "ApiResponse",
    "ErrorResponse",
    # Auth
    "LoginRequest",
    "TokenResponse",
    "TokenRefreshResponse",
    "RefreshTokenRequest",
    "LogoutRequest",
    "LogoutResponse",
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserInDB",
    "UserListResponse",
    "RoleResponse",
    # Project
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectInDB",
    "ProjectListResponse",
    "ProjectMemberCreate",
    "ProjectMemberResponse",
    "ProjectMemberListResponse",
    # Stats
    "TokenTrendResponse",
    "ActivityTrendResponse",
    "TopUserResponse",
    "ProjectStatsResponse",
    "CodeRankResponse",
    "BugTrendResponse",
    "AIAdoptionResponse",
    "PersonalCodeStatsResponse",
    "PersonalTokenStatsResponse",
    "PersonalBugRateResponse",
    # Sync
    "SyncTaskCreate",
    "SyncTaskResponse",
    "SyncTaskListResponse",
]
