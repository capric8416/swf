"""Project schemas for request/response validation."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectBase(BaseModel):
    """Base project schema with common attributes."""

    name: str = Field(..., min_length=1, max_length=100, description="项目名称")
    code: str = Field(..., min_length=1, max_length=50, description="项目编号")
    description: str | None = Field(None, max_length=1000, description="项目描述")
    stage: str = Field(..., description="项目阶段")
    status: str = Field(default="active", description="项目状态")
    start_date: date | None = Field(None, description="开始日期")
    end_date: date | None = Field(None, description="结束日期")


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""

    pass


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project."""

    name: str | None = Field(None, min_length=1, max_length=100)
    code: str | None = Field(None, min_length=1, max_length=50)
    description: str | None = Field(None, max_length=1000)
    stage: str | None = None
    status: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class ProjectInDB(ProjectBase):
    """Schema for project as stored in database."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    manager_id: int | None = None
    created_at: datetime
    updated_at: datetime


class ProjectResponse(BaseModel):
    """Schema for project response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    description: str | None = None
    stage: str
    status: str
    start_date: date | None = None
    end_date: date | None = None
    manager_id: int | None = None
    created_at: datetime
    updated_at: datetime
    members: list["ProjectMemberResponse"] = []


class ProjectListResponse(BaseModel):
    """Schema for paginated project list response."""

    items: list[ProjectInDB]
    total: int
    page: int
    page_size: int


class ProjectMemberBase(BaseModel):
    """Base project member schema."""

    user_id: int = Field(..., description="用户ID")
    role: str = Field(default="developer", description="成员角色")


class ProjectMemberCreate(ProjectMemberBase):
    """Schema for adding a member to a project."""

    pass


class ProjectMemberInDB(ProjectMemberBase):
    """Schema for project member as stored in database."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    joined_at: datetime


class ProjectMemberResponse(ProjectMemberInDB):
    """Schema for project member response with user details."""

    username: str | None = None
    email: str | None = None


class ProjectMemberListResponse(BaseModel):
    """Schema for paginated project member list response."""

    items: list[ProjectMemberResponse]
    total: int
    page: int
    page_size: int


# Resolve forward references
ProjectResponse.model_rebuild()
