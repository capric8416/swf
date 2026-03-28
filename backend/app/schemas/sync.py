"""Sync schemas for request/response validation."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class SyncGitLabRequest(BaseModel):
    """Schema for GitLab sync request."""

    project_ids: list[int] | None = Field(None, description="项目ID列表（为空则同步所有）")
    start_date: date | None = Field(None, description="开始日期")
    end_date: date | None = Field(None, description="结束日期")


class SyncTraeRequest(BaseModel):
    """Schema for Trae sync request."""

    user_ids: list[int] | None = Field(None, description="用户ID列表（为空则同步所有）")
    start_date: date | None = Field(None, description="开始日期")
    end_date: date | None = Field(None, description="结束日期")


class SyncZendaoRequest(BaseModel):
    """Schema for Zendao sync request."""

    project_ids: list[int] | None = Field(None, description="项目ID列表（为空则同步所有）")
    start_date: date | None = Field(None, description="开始日期")
    end_date: date | None = Field(None, description="结束日期")


class SyncTaskResponse(BaseModel):
    """Schema for sync task response."""

    task_id: str = Field(..., description="任务ID")
    source: str = Field(..., description="同步来源")
    status: str = Field(..., description="任务状态")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    message: str | None = Field(None, description="状态消息")


class SyncTaskInDB(BaseModel):
    """Schema for sync task in database."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    source: str
    status: str
    params: dict | None = None
    result: dict | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class SyncTaskListResponse(BaseModel):
    """Schema for sync task list response."""

    items: list[SyncTaskInDB]
    total: int
    page: int
    page_size: int


class SyncLogResponse(BaseModel):
    """Schema for sync log response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: str
    level: str
    message: str
    details: dict | None = None
    created_at: datetime


class SyncLogListResponse(BaseModel):
    """Schema for sync log list response."""

    items: list[SyncLogResponse]
    total: int
    page: int
    page_size: int
