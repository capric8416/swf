"""Data Synchronization API routes."""

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_admin_permission
from app.db.base import get_db
from app.db.models import User
from app.schemas.sync import (
    SyncGitLabRequest,
    SyncLogListResponse,
    SyncLogResponse,
    SyncTaskInDB,
    SyncTaskListResponse,
    SyncTaskResponse,
    SyncTraeRequest,
    SyncZendaoRequest,
)

router = APIRouter(tags=["sync"])

# In-memory storage for sync tasks (in production, use database)
_sync_tasks: dict[str, dict] = {}
_sync_logs: list[dict] = []


def create_sync_task(source: str, params: dict) -> SyncTaskResponse:
    """Create a new sync task."""
    task_id = str(uuid4())
    task = {
        "id": task_id,
        "source": source,
        "status": "pending",
        "params": params,
        "result": None,
        "error_message": None,
        "started_at": None,
        "completed_at": None,
        "created_at": datetime.utcnow(),
    }
    _sync_tasks[task_id] = task

    return SyncTaskResponse(
        task_id=task_id,
        source=source,
        status="pending",
        message="Sync task created successfully",
    )


@router.post("/gitlab", response_model=SyncTaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def sync_gitlab(
    sync_data: SyncGitLabRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_permission),
) -> SyncTaskResponse:
    """Trigger GitLab data synchronization."""
    params = sync_data.model_dump(exclude_none=True)
    return create_sync_task("gitlab", params)


@router.post("/trae", response_model=SyncTaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def sync_trae(
    sync_data: SyncTraeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_permission),
) -> SyncTaskResponse:
    """Trigger Trae data synchronization."""
    params = sync_data.model_dump(exclude_none=True)
    return create_sync_task("trae", params)


@router.post("/zendao", response_model=SyncTaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def sync_zendao(
    sync_data: SyncZendaoRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_permission),
) -> SyncTaskResponse:
    """Trigger Zendao data synchronization."""
    params = sync_data.model_dump(exclude_none=True)
    return create_sync_task("zendao", params)


@router.get("/tasks", response_model=SyncTaskListResponse)
async def list_sync_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: str | None = Query(None, description="按状态筛选"),
    source: str | None = Query(None, description="按来源筛选"),
    db: AsyncSession = Depends(get_db),
) -> SyncTaskListResponse:
    """Get list of sync tasks."""
    # Filter tasks
    tasks = list(_sync_tasks.values())

    if status:
        tasks = [t for t in tasks if t["status"] == status]
    if source:
        tasks = [t for t in tasks if t["source"] == source]

    # Sort by created_at descending
    tasks.sort(key=lambda x: x["created_at"], reverse=True)

    # Paginate
    total = len(tasks)
    offset = (page - 1) * page_size
    paginated_tasks = tasks[offset : offset + page_size]

    return SyncTaskListResponse(
        items=[SyncTaskInDB.model_validate(t) for t in paginated_tasks],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/logs", response_model=SyncLogListResponse)
async def list_sync_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    task_id: str | None = Query(None, description="任务ID"),
    level: str | None = Query(None, description="日志级别"),
    db: AsyncSession = Depends(get_db),
) -> SyncLogListResponse:
    """Get sync logs."""
    # Filter logs
    logs = _sync_logs.copy()

    if task_id:
        logs = [l for l in logs if l["task_id"] == task_id]
    if level:
        # Filter by level (error and above)
        level_priority = {"debug": 0, "info": 1, "warning": 2, "error": 3, "critical": 4}
        min_priority = level_priority.get(level, 0)
        logs = [
            l for l in logs if level_priority.get(l["level"], 0) >= min_priority
        ]

    # Sort by created_at descending
    logs.sort(key=lambda x: x["created_at"], reverse=True)

    # Paginate
    total = len(logs)
    offset = (page - 1) * page_size
    paginated_logs = logs[offset : offset + page_size]

    return SyncLogListResponse(
        items=[SyncLogResponse.model_validate(l) for l in paginated_logs],
        total=total,
        page=page,
        page_size=page_size,
    )
