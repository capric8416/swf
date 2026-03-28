"""Project Statistics API routes."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.db.models import Project, ProjectMember, User
from app.schemas.stats import (
    AIAdoptionResponse,
    BugTrendResponse,
    CodeRankResponse,
    ProjectStatsResponse,
)

router = APIRouter(tags=["project-stats"])


def generate_date_range(start_date: date, end_date: date) -> list[str]:
    """Generate a list of dates between start and end."""
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current.isoformat())
        current += timedelta(days=1)
    return dates


async def verify_project_exists(project_id: int, db: AsyncSession) -> Project:
    """Verify project exists and return it."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found",
        )

    return project


@router.get("/{project_id}", response_model=ProjectStatsResponse)
async def get_project_stats(
    project_id: int,
    db: AsyncSession = Depends(get_db),
) -> ProjectStatsResponse:
    """Get project statistics overview."""
    project = await verify_project_exists(project_id, db)

    # Get active member count
    member_count_result = await db.execute(
        select(func.count())
        .select_from(ProjectMember)
        .where(ProjectMember.project_id == project_id)
    )
    active_members = member_count_result.scalar() or 0

    # For now, return mock data
    # In production, this would query actual statistics tables
    import random

    return ProjectStatsResponse(
        project_id=project.id,
        project_name=project.name,
        total_commits=random.randint(100, 1000),
        total_tokens=random.randint(10000, 1000000),
        active_members=active_members,
        bug_count=random.randint(0, 50),
    )


@router.get("/{project_id}/code-rank", response_model=list[CodeRankResponse])
async def get_project_code_rank(
    project_id: int,
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    db: AsyncSession = Depends(get_db),
) -> list[CodeRankResponse]:
    """Get code line ranking for project members."""
    await verify_project_exists(project_id, db)

    # Get project members
    result = await db.execute(
        select(ProjectMember, User)
        .join(User, ProjectMember.user_id == User.id)
        .where(ProjectMember.project_id == project_id)
        .limit(limit)
    )

    # For now, return mock data based on members
    import random

    rankings = []
    for member, user in result.all():
        lines_added = random.randint(1000, 50000)
        lines_deleted = random.randint(100, 10000)
        rankings.append(
            CodeRankResponse(
                user_id=user.id,
                username=user.username,
                lines_added=lines_added,
                lines_deleted=lines_deleted,
                total_lines=lines_added - lines_deleted,
            )
        )

    # Sort by total lines descending
    rankings.sort(key=lambda x: x.total_lines, reverse=True)

    return rankings


@router.get("/{project_id}/bug-trend", response_model=BugTrendResponse)
async def get_project_bug_trend(
    project_id: int,
    start_date: date | None = Query(None, description="开始日期"),
    end_date: date | None = Query(None, description="结束日期"),
    db: AsyncSession = Depends(get_db),
) -> BugTrendResponse:
    """Get bug trend for a project."""
    await verify_project_exists(project_id, db)

    # Set default date range (last 30 days)
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=29)

    dates = generate_date_range(start_date, end_date)

    # For now, return mock data
    import random

    created = [random.randint(0, 10) for _ in dates]
    resolved = [random.randint(0, 8) for _ in dates]

    return BugTrendResponse(dates=dates, created=created, resolved=resolved)


@router.get("/{project_id}/ai-adoption", response_model=list[AIAdoptionResponse])
async def get_project_ai_adoption(
    project_id: int,
    days: int = Query(30, ge=7, le=365, description="天数"),
    db: AsyncSession = Depends(get_db),
) -> list[AIAdoptionResponse]:
    """Get AI adoption rate for a project."""
    await verify_project_exists(project_id, db)

    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    dates = generate_date_range(start_date, end_date)

    # For now, return mock data
    import random

    adoption_data = []
    for date_str in dates:
        ai_suggestions = random.randint(10, 200)
        accepted_suggestions = random.randint(0, ai_suggestions)
        adoption_rate = (
            (accepted_suggestions / ai_suggestions * 100) if ai_suggestions > 0 else 0
        )

        adoption_data.append(
            AIAdoptionResponse(
                date=date_str,
                adoption_rate=round(adoption_rate, 2),
                ai_suggestions=ai_suggestions,
                accepted_suggestions=accepted_suggestions,
            )
        )

    return adoption_data
