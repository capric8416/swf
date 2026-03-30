"""Personal Statistics API routes."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.db.models import Project, User
from app.schemas.stats import (
    PersonalBugRateResponse,
    PersonalCodeStatsResponse,
    PersonalTokenStatsResponse,
)
from app.services.code_stats_service import CodeStatsService
from app.services.token_stats_service import TokenStatsService
from app.services.bug_stats_service import BugStatsService
from app.core.dependencies import get_code_stats_service, get_token_stats_service, get_bug_stats_service

router = APIRouter(tags=["personal-stats"])


async def verify_user_exists(user_id: int, db: AsyncSession) -> User:
    """Verify user exists and return it."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )

    return user


@router.get("/code", response_model=PersonalCodeStatsResponse)
async def get_personal_code_stats(
    user_id: int = Query(..., description="用户ID"),
    start_date: date | None = Query(None, description="开始日期"),
    end_date: date | None = Query(None, description="结束日期"),
    db: AsyncSession = Depends(get_db),
    code_stats_service: CodeStatsService = Depends(get_code_stats_service),
) -> PersonalCodeStatsResponse:
    """Get personal code statistics."""
    await verify_user_exists(user_id, db)

    # Set default date range (last 30 days)
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=29)

    # Calculate days difference
    days_diff = (end_date - start_date).days + 1

    # Get real statistics from database
    stats = await code_stats_service.calculate_code_stats(
        db=db,
        user_id=user_id,
        project_id=None,
        start_date=start_date,
        end_date=end_date,
    )

    # Calculate average commits per day
    avg_commits_per_day = round(stats.total_commits / days_diff, 2) if days_diff > 0 else 0.0

    return PersonalCodeStatsResponse(
        total_commits=stats.total_commits,
        total_prs=0,  # PR data not tracked in current model
        lines_added=stats.total_additions,
        lines_deleted=stats.total_deletions,
        avg_commits_per_day=avg_commits_per_day,
    )


@router.get("/token", response_model=PersonalTokenStatsResponse)
async def get_personal_token_stats(
    user_id: int = Query(..., description="用户ID"),
    start_date: date | None = Query(None, description="开始日期"),
    end_date: date | None = Query(None, description="结束日期"),
    db: AsyncSession = Depends(get_db),
    token_stats_service: TokenStatsService = Depends(get_token_stats_service),
) -> PersonalTokenStatsResponse:
    """Get personal token usage statistics."""
    await verify_user_exists(user_id, db)

    # Set default date range (last 30 days)
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=29)

    # Calculate days difference
    days_diff = (end_date - start_date).days + 1

    # Get real token usage from database
    token_summary = await token_stats_service.get_user_token_usage(
        db=db,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )

    # Split total tokens into prompt/completion (60/40 split as estimate)
    total_tokens = token_summary.total_tokens
    prompt_tokens = int(total_tokens * 0.6)
    completion_tokens = total_tokens - prompt_tokens

    # Calculate average tokens per day
    avg_tokens_per_day = round(total_tokens / days_diff, 2) if days_diff > 0 else 0.0

    return PersonalTokenStatsResponse(
        total_tokens=total_tokens,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        avg_tokens_per_day=avg_tokens_per_day,
    )


@router.get("/bug-rate", response_model=PersonalBugRateResponse)
async def get_personal_bug_rate(
    user_id: int = Query(..., description="用户ID"),
    project_id: int | None = Query(None, description="项目ID（可选）"),
    db: AsyncSession = Depends(get_db),
    bug_stats_service: BugStatsService = Depends(get_bug_stats_service),
    code_stats_service: CodeStatsService = Depends(get_code_stats_service),
) -> PersonalBugRateResponse:
    """Get personal bug rate statistics."""
    await verify_user_exists(user_id, db)

    # If project_id is provided, verify project exists
    if project_id:
        project_result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        if not project_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found",
            )

    # Get real bug statistics from database
    end_date = date.today()
    start_date = end_date - timedelta(days=29)

    bug_stats = await bug_stats_service.get_bug_stats_by_user(
        db=db,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )

    # Calculate bug rate (bugs per 1000 lines of code)
    # Estimate lines of code from commits (assuming 100 lines per commit on average)
    code_stats = await code_stats_service.calculate_code_stats(
        db=db,
        user_id=user_id,
        project_id=project_id,
        start_date=start_date,
        end_date=end_date,
    )

    estimated_lines = code_stats.total_additions
    bug_rate = (
        round((bug_stats.total_bugs / estimated_lines) * 1000, 2)
        if estimated_lines > 0
        else 0.0
    )

    return PersonalBugRateResponse(
        total_bugs=bug_stats.total_bugs,
        critical_bugs=bug_stats.critical_bugs,
        bug_rate=bug_rate,
        resolved_bugs=bug_stats.resolved_bugs,
    )
