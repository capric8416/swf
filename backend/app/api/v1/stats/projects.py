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
from app.services.code_stats_service import CodeStatsService
from app.services.token_stats_service import TokenStatsService
from app.services.bug_stats_service import BugStatsService
from app.core.dependencies import get_code_stats_service, get_token_stats_service, get_bug_stats_service

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
    code_stats_service: CodeStatsService = Depends(get_code_stats_service),
    token_stats_service: TokenStatsService = Depends(get_token_stats_service),
    bug_stats_service: BugStatsService = Depends(get_bug_stats_service),
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

    # Get code statistics for the last 30 days
    end_date = date.today()
    start_date = end_date - timedelta(days=29)

    code_stats = await code_stats_service.calculate_code_stats(
        db=db,
        user_id=None,
        project_id=project_id,
        start_date=start_date,
        end_date=end_date,
    )

    # Get token usage statistics
    token_summary = await token_stats_service.get_project_token_usage(
        db=db,
        project_id=project_id,
        start_date=start_date,
        end_date=end_date,
    )

    # Get bug statistics
    bug_stats = await bug_stats_service.get_bug_stats_by_project(
        db=db,
        project_id=project_id,
        start_date=start_date,
        end_date=end_date,
    )

    return ProjectStatsResponse(
        project_id=project.id,
        project_name=project.name,
        total_commits=code_stats.total_commits,
        total_tokens=token_summary.total_tokens,
        active_members=active_members,
        bug_count=bug_stats.total_bugs,
    )


@router.get("/{project_id}/code-rank", response_model=list[CodeRankResponse])
async def get_project_code_rank(
    project_id: int,
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    db: AsyncSession = Depends(get_db),
    code_stats_service: CodeStatsService = Depends(get_code_stats_service),
) -> list[CodeRankResponse]:
    """Get code line ranking for project members."""
    await verify_project_exists(project_id, db)

    # Get real code ranking from database
    rankings = await code_stats_service.get_user_code_ranking(
        db=db,
        project_id=project_id,
        limit=limit,
    )

    return [
        CodeRankResponse(
            user_id=rank["user_id"],
            username=rank["username"],
            lines_added=rank["lines_added"],
            lines_deleted=rank["lines_deleted"],
            total_lines=rank["total_lines"],
        )
        for rank in rankings
    ]


@router.get("/{project_id}/bug-trend", response_model=BugTrendResponse)
async def get_project_bug_trend(
    project_id: int,
    start_date: date | None = Query(None, description="开始日期"),
    end_date: date | None = Query(None, description="结束日期"),
    db: AsyncSession = Depends(get_db),
    bug_stats_service: BugStatsService = Depends(get_bug_stats_service),
) -> BugTrendResponse:
    """Get bug trend for a project."""
    await verify_project_exists(project_id, db)

    # Set default date range (last 30 days)
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=29)

    dates = generate_date_range(start_date, end_date)

    # Get real bug trends from database
    days = (end_date - start_date).days + 1
    bug_trends = await bug_stats_service.get_bug_trends(
        db=db,
        project_id=project_id,
        days=days,
    )

    # Filter to the requested date range
    start_idx = (start_date - (end_date - timedelta(days=days - 1))).days
    end_idx = start_idx + len(dates)
    filtered_trends = bug_trends[start_idx:end_idx] if start_idx >= 0 else bug_trends[:len(dates)]

    created = [trend.created for trend in filtered_trends]
    resolved = [trend.resolved for trend in filtered_trends]

    return BugTrendResponse(dates=dates, created=created, resolved=resolved)


@router.get("/{project_id}/ai-adoption", response_model=list[AIAdoptionResponse])
async def get_project_ai_adoption(
    project_id: int,
    days: int = Query(30, ge=7, le=365, description="天数"),
    db: AsyncSession = Depends(get_db),
    code_stats_service: CodeStatsService = Depends(get_code_stats_service),
) -> list[AIAdoptionResponse]:
    """Get AI adoption rate for a project."""
    await verify_project_exists(project_id, db)

    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    dates = generate_date_range(start_date, end_date)

    # Get commit trends to calculate AI adoption
    commit_trends = await code_stats_service.get_commit_trends(
        db=db,
        user_id=None,
        project_id=project_id,
        days=days,
    )

    # Create adoption data based on AI-generated commits
    adoption_data = []
    for i, date_str in enumerate(dates):
        if i < len(commit_trends):
            trend = commit_trends[i]
            # For now, estimate AI suggestions based on commit data
            # In a real implementation, this would query AISuggestion table
            ai_suggestions = trend.commit_count
            accepted_suggestions = trend.commit_count  # Assume all commits are accepted
            adoption_rate = 100.0 if ai_suggestions > 0 else 0.0
        else:
            ai_suggestions = 0
            accepted_suggestions = 0
            adoption_rate = 0.0

        adoption_data.append(
            AIAdoptionResponse(
                date=date_str,
                adoption_rate=round(adoption_rate, 2),
                ai_suggestions=ai_suggestions,
                accepted_suggestions=accepted_suggestions,
            )
        )

    return adoption_data
