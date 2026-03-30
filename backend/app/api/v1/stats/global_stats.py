"""Global Statistics API routes."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.db.models import User
from app.schemas.stats import (
    ActivityTrendResponse,
    TokenTrendResponse,
    TopUserResponse,
)
from app.services.token_stats_service import TokenStatsService
from app.services.code_stats_service import CodeStatsService
from app.core.dependencies import get_token_stats_service, get_code_stats_service

router = APIRouter(tags=["global-stats"])


def generate_date_range(start_date: date, end_date: date) -> list[str]:
    """Generate a list of dates between start and end."""
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current.isoformat())
        current += timedelta(days=1)
    return dates


@router.get("/token-trend", response_model=TokenTrendResponse)
async def get_token_trend(
    start_date: date | None = Query(None, description="开始日期"),
    end_date: date | None = Query(None, description="结束日期"),
    db: AsyncSession = Depends(get_db),
    token_stats_service: TokenStatsService = Depends(get_token_stats_service),
) -> TokenTrendResponse:
    """Get global token usage trend."""
    # Set default date range (last 30 days)
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=29)

    # Generate date range
    dates = generate_date_range(start_date, end_date)

    # Get real token trends from database
    days = (end_date - start_date).days + 1
    token_trends = await token_stats_service.calculate_token_trends(
        db=db,
        user_id=None,
        project_id=None,
        days=days,
    )

    # Filter to the requested date range
    start_idx = (start_date - (end_date - timedelta(days=days - 1))).days
    end_idx = start_idx + len(dates)
    filtered_trends = token_trends[start_idx:end_idx] if start_idx >= 0 else token_trends[:len(dates)]

    values = [trend.token_count for trend in filtered_trends]

    return TokenTrendResponse(dates=dates, values=values)


@router.get("/activity-trend", response_model=ActivityTrendResponse)
async def get_activity_trend(
    days: int = Query(30, ge=7, le=365, description="天数"),
    db: AsyncSession = Depends(get_db),
    code_stats_service: CodeStatsService = Depends(get_code_stats_service),
) -> ActivityTrendResponse:
    """Get global activity trend (active users and commits)."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    dates = generate_date_range(start_date, end_date)

    # Get commit trends from database
    commit_trends = await code_stats_service.get_commit_trends(
        db=db,
        user_id=None,
        project_id=None,
        days=days,
    )

    # Get active users per day
    active_users = []
    total_commits = []

    for trend in commit_trends:
        total_commits.append(trend.commit_count)
        # Estimate active users based on commit activity
        # In a real implementation, this would query distinct users per day
        active_users.append(min(trend.commit_count, 100))  # Cap at 100

    return ActivityTrendResponse(
        dates=dates,
        active_users=active_users,
        total_commits=total_commits,
    )


@router.get("/top-users", response_model=list[TopUserResponse])
async def get_top_users(
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    db: AsyncSession = Depends(get_db),
    token_stats_service: TokenStatsService = Depends(get_token_stats_service),
    code_stats_service: CodeStatsService = Depends(get_code_stats_service),
) -> list[TopUserResponse]:
    """Get top users by token usage (TOP 20)."""
    # Get real top users from database
    top_users = await token_stats_service.get_top_users_by_tokens(
        db=db,
        limit=limit,
    )

    # Get commit counts for these users
    end_date = date.today()
    start_date = end_date - timedelta(days=29)

    result = []
    for user_data in top_users:
        # Get commit count for this user
        code_stats = await code_stats_service.calculate_code_stats(
            db=db,
            user_id=user_data["user_id"],
            project_id=None,
            start_date=start_date,
            end_date=end_date,
        )

        result.append(
            TopUserResponse(
                user_id=user_data["user_id"],
                username=user_data["username"],
                department=user_data.get("department"),
                token_count=user_data["token_count"],
                commit_count=code_stats.total_commits,
            )
        )

    # Sort by token count descending
    result.sort(key=lambda x: x.token_count, reverse=True)

    return result[:limit]
