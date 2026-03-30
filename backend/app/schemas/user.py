"""User schemas for request/response validation."""

from pydantic import BaseModel, Field, field_validator


class RoleResponse(BaseModel):
    """Role response schema."""

    id: int = Field(..., description="角色ID")
    name: str = Field(..., description="角色名称")
    description: str | None = Field(None, description="角色描述")
    permissions: list[str] = Field(default_factory=list, description="权限列表")

    class Config:
        """Pydantic config."""

        from_attributes = True


class UserBase(BaseModel):
    """Base user schema with common fields."""

    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    department: str = Field(..., description="部门")


class UserCreate(UserBase):
    """User creation schema."""

    password: str = Field(..., min_length=6, description="密码")
    role_id: int | None = Field(None, description="角色ID")


class UserUpdate(BaseModel):
    """User update schema."""

    email: str | None = Field(None, description="邮箱")
    department: str | None = Field(None, description="部门")
    is_active: bool | None = Field(None, description="是否激活")
    role_id: int | None = Field(None, description="角色ID")


class UserResponse(UserBase):
    """User response schema."""

    id: int = Field(..., description="用户ID")
    is_active: bool = Field(..., description="是否激活")
    role_id: int | None = Field(None, description="角色ID")
    role: RoleResponse | None = Field(None, description="角色信息")

    class Config:
        """Pydantic config."""

        from_attributes = True


class UserInDB(UserResponse):
    """User in database schema (includes timestamps)."""

    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    last_login_at: str | None = Field(None, description="最后登录时间")

    class Config:
        """Pydantic config."""

        from_attributes = True


class UserListResponse(BaseModel):
    """User list response schema."""

    items: list[UserResponse] = Field(default_factory=list, description="用户列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    page_size: int = Field(..., description="每页数量")
