"""Global Statistics API routes."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.db.models import User
from app.schemas.stats import (
    ActivityTrendResponse,
    TokenTrendResponse,
    TopUserResponse,
)

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
) -> TokenTrendResponse:
    """Get global token usage trend."""
    # Set default date range (last 30 days)
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=29)

    # Generate date range
    dates = generate_date_range(start_date, end_date)

    # For now, return mock data
    # In production, this would query actual token usage statistics
    import random

    values = [random.randint(1000, 50000) for _ in dates]

    return TokenTrendResponse(dates=dates, values=values)


@router.get("/activity-trend", response_model=ActivityTrendResponse)
async def get_activity_trend(
    days: int = Query(30, ge=7, le=365, description="天数"),
    db: AsyncSession = Depends(get_db),
) -> ActivityTrendResponse:
    """Get global activity trend (active users and commits)."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    dates = generate_date_range(start_date, end_date)

    # For now, return mock data
    import random

    active_users = [random.randint(10, 100) for _ in dates]
    total_commits = [random.randint(50, 500) for _ in dates]

    return ActivityTrendResponse(
        dates=dates,
        active_users=active_users,
        total_commits=total_commits,
    )


@router.get("/top-users", response_model=list[TopUserResponse])
async def get_top_users(
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    db: AsyncSession = Depends(get_db),
) -> list[TopUserResponse]:
    """Get top users by token usage (TOP 20)."""
    # Query all active users
    result = await db.execute(
        select(User)
        .where(User.is_active == True)
        .limit(limit)
    )
    users = result.scalars().all()

    # For now, return mock data based on users
    # In production, this would aggregate actual token usage
    import random

    top_users = []
    for user in users:
        top_users.append(
            TopUserResponse(
                user_id=user.id,
                username=user.username,
                department=user.department,
                token_count=random.randint(10000, 1000000),
                commit_count=random.randint(10, 500),
            )
        )

    # Sort by token count descending
    top_users.sort(key=lambda x: x.token_count, reverse=True)

    return top_users[:limit]
