"""Statistics schemas for request/response validation."""


from pydantic import BaseModel, Field


class TokenTrendResponse(BaseModel):
    """Schema for token usage trend response."""

    dates: list[str] = Field(default_factory=list, description="日期列表")
    values: list[int] = Field(default_factory=list, description="Token使用量列表")


class ActivityTrendResponse(BaseModel):
    """Schema for activity trend response."""

    dates: list[str] = Field(default_factory=list, description="日期列表")
    active_users: list[int] = Field(default_factory=list, description="活跃用户数列表")
    total_commits: list[int] = Field(default_factory=list, description="提交数列表")


class TopUserResponse(BaseModel):
    """Schema for top user response."""

    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    department: str | None = Field(None, description="部门")
    token_count: int = Field(default=0, description="Token使用量")
    commit_count: int = Field(default=0, description="提交次数")


class ProjectStatsResponse(BaseModel):
    """Schema for project statistics response."""

    project_id: int = Field(..., description="项目ID")
    project_name: str = Field(..., description="项目名称")
    total_commits: int = Field(default=0, description="总提交数")
    total_tokens: int = Field(default=0, description="总Token使用量")
    active_members: int = Field(default=0, description="活跃成员数")
    bug_count: int = Field(default=0, description="Bug数量")


class CodeRankResponse(BaseModel):
    """Schema for code rank response."""

    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    lines_added: int = Field(default=0, description="新增代码行数")
    lines_deleted: int = Field(default=0, description="删除代码行数")
    total_lines: int = Field(default=0, description="总代码行数")


class BugTrendResponse(BaseModel):
    """Schema for bug trend response."""

    dates: list[str] = Field(default_factory=list, description="日期列表")
    created: list[int] = Field(default_factory=list, description="创建的Bug数")
    resolved: list[int] = Field(default_factory=list, description="解决的Bug数")


class AIAdoptionResponse(BaseModel):
    """Schema for AI adoption rate response."""

    date: str = Field(..., description="日期")
    adoption_rate: float = Field(default=0.0, description="采纳率(0-100)")
    ai_suggestions: int = Field(default=0, description="AI建议数")
    accepted_suggestions: int = Field(default=0, description="接受的建议数")


class PersonalCodeStatsResponse(BaseModel):
    """Schema for personal code statistics response."""

    total_commits: int = Field(default=0, description="总提交数")
    total_prs: int = Field(default=0, description="总PR数")
    lines_added: int = Field(default=0, description="新增代码行数")
    lines_deleted: int = Field(default=0, description="删除代码行数")
    avg_commits_per_day: float = Field(default=0.0, description="日均提交数")


class PersonalTokenStatsResponse(BaseModel):
    """Schema for personal token statistics response."""

    total_tokens: int = Field(default=0, description="总Token使用量")
    prompt_tokens: int = Field(default=0, description="Prompt Token使用量")
    completion_tokens: int = Field(default=0, description="Completion Token使用量")
    avg_tokens_per_day: float = Field(default=0.0, description="日均Token使用量")


class PersonalBugRateResponse(BaseModel):
    """Schema for personal bug rate response."""

    total_bugs: int = Field(default=0, description="Bug总数")
    critical_bugs: int = Field(default=0, description="严重Bug数")
    bug_rate: float = Field(default=0.0, description="Bug率")
    resolved_bugs: int = Field(default=0, description="已解决Bug数")
