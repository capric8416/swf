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

    # For now, return mock data
    # In production, this would query actual git commit statistics
    import random

    total_commits = random.randint(10, 200)

    return PersonalCodeStatsResponse(
        total_commits=total_commits,
        total_prs=random.randint(5, 50),
        lines_added=random.randint(1000, 50000),
        lines_deleted=random.randint(100, 10000),
        avg_commits_per_day=round(total_commits / days_diff, 2),
    )


@router.get("/token", response_model=PersonalTokenStatsResponse)
async def get_personal_token_stats(
    user_id: int = Query(..., description="用户ID"),
    start_date: date | None = Query(None, description="开始日期"),
    end_date: date | None = Query(None, description="结束日期"),
    db: AsyncSession = Depends(get_db),
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

    # For now, return mock data
    # In production, this would query actual token usage statistics
    import random

    prompt_tokens = random.randint(10000, 500000)
    completion_tokens = random.randint(5000, 200000)
    total_tokens = prompt_tokens + completion_tokens

    return PersonalTokenStatsResponse(
        total_tokens=total_tokens,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        avg_tokens_per_day=round(total_tokens / days_diff, 2),
    )


@router.get("/bug-rate", response_model=PersonalBugRateResponse)
async def get_personal_bug_rate(
    user_id: int = Query(..., description="用户ID"),
    project_id: int | None = Query(None, description="项目ID（可选）"),
    db: AsyncSession = Depends(get_db),
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

    # For now, return mock data
    # In production, this would query actual bug statistics from Zendao
    import random

    total_bugs = random.randint(0, 20)
    critical_bugs = random.randint(0, min(5, total_bugs))
    resolved_bugs = random.randint(0, total_bugs)

    # Calculate bug rate (bugs per 1000 lines of code, mock calculation)
    bug_rate = round(total_bugs * random.uniform(0.1, 1.0), 2)

    return PersonalBugRateResponse(
        total_bugs=total_bugs,
        critical_bugs=critical_bugs,
        bug_rate=bug_rate,
        resolved_bugs=resolved_bugs,
    )
