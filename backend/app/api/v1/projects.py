"""Project API routes."""


from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.db.models import Project, ProjectMember, User
from app.schemas.project import (
    ProjectCreate,
    ProjectInDB,
    ProjectListResponse,
    ProjectMemberCreate,
    ProjectMemberListResponse,
    ProjectMemberResponse,
    ProjectResponse,
    ProjectUpdate,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: str | None = Query(None, description="按状态筛选"),
    stage: str | None = Query(None, description="按阶段筛选"),
    keyword: str | None = Query(None, description="搜索关键词"),
    db: AsyncSession = Depends(get_db),
) -> ProjectListResponse:
    """Get paginated list of projects with optional filtering."""
    # Build base query
    query = select(Project)
    count_query = select(func.count()).select_from(Project)

    # Apply filters
    filters = []
    if status:
        filters.append(Project.status == status)
    if stage:
        filters.append(Project.stage == stage)
    if keyword:
        filters.append(
            (Project.name.contains(keyword)) | (Project.code.contains(keyword))
        )

    if filters:
        for f in filters:
            query = query.where(f)
            count_query = count_query.where(f)

    # Get total count
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    projects = result.scalars().all()

    return ProjectListResponse(
        items=[ProjectInDB.model_validate(p) for p in projects],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ProjectInDB, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
) -> ProjectInDB:
    """Create a new project."""
    # Check for duplicate code
    existing = await db.execute(
        select(Project).where(Project.code == project_data.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Project with code '{project_data.code}' already exists",
        )

    # Create project
    project = Project(**project_data.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)

    return ProjectInDB.model_validate(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Get project details by ID."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found",
        )

    # Get members with user details
    members_result = await db.execute(
        select(ProjectMember, User)
        .join(User, ProjectMember.user_id == User.id)
        .where(ProjectMember.project_id == project_id)
    )
    members = []
    for member, user in members_result.all():
        member_data = ProjectMemberResponse.model_validate(member)
        member_data.username = user.username
        member_data.email = user.email
        members.append(member_data)

    # Build response manually to avoid lazy loading issues
    return ProjectResponse(
        id=project.id,
        name=project.name,
        code=project.code,
        description=project.description,
        stage=project.stage,
        status=project.status,
        start_date=project.start_date,
        end_date=project.end_date,
        manager_id=project.manager_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
        members=members,
    )


@router.put("/{project_id}", response_model=ProjectInDB)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
) -> ProjectInDB:
    """Update an existing project."""
    # Get existing project
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found",
        )

    # Check for duplicate code if updating code
    if project_data.code and project_data.code != project.code:
        existing = await db.execute(
            select(Project).where(
                (Project.code == project_data.code) & (Project.id != project_id)
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Project with code '{project_data.code}' already exists",
            )

    # Update fields
    update_data = project_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)

    return ProjectInDB.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a project."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found",
        )

    await db.delete(project)
    await db.commit()


@router.get("/{project_id}/members", response_model=ProjectMemberListResponse)
async def list_project_members(
    project_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> ProjectMemberListResponse:
    """Get members of a project."""
    # Check project exists
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found",
        )

    # Get total count
    count_result = await db.execute(
        select(func.count())
        .select_from(ProjectMember)
        .where(ProjectMember.project_id == project_id)
    )
    total = count_result.scalar() or 0

    # Get members with user details
    offset = (page - 1) * page_size
    members_result = await db.execute(
        select(ProjectMember, User)
        .join(User, ProjectMember.user_id == User.id)
        .where(ProjectMember.project_id == project_id)
        .offset(offset)
        .limit(page_size)
    )

    members = []
    for member, user in members_result.all():
        member_data = ProjectMemberResponse.model_validate(member)
        member_data.username = user.username
        member_data.email = user.email
        members.append(member_data)

    return ProjectMemberListResponse(
        items=members,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_project_member(
    project_id: int,
    member_data: ProjectMemberCreate,
    db: AsyncSession = Depends(get_db),
) -> ProjectMemberResponse:
    """Add a member to a project."""
    # Check project exists
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found",
        )

    # Check user exists
    user_result = await db.execute(
        select(User).where(User.id == member_data.user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {member_data.user_id} not found",
        )

    # Check if already a member
    existing = await db.execute(
        select(ProjectMember).where(
            (ProjectMember.project_id == project_id)
            & (ProjectMember.user_id == member_data.user_id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this project",
        )

    # Create membership
    member = ProjectMember(
        project_id=project_id,
        user_id=member_data.user_id,
        role=member_data.role,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)

    response = ProjectMemberResponse.model_validate(member)
    response.username = user.username
    response.email = user.email
    return response
