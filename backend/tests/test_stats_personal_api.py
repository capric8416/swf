"""Tests for Personal Stats API - TDD Red Phase.

These tests define the expected behavior of the personal statistics API endpoints.
"""

from datetime import date, timedelta

import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient


@pytest.fixture
def app(session) -> FastAPI:
    """Create test FastAPI app with routes and overridden dependencies."""
    from fastapi import FastAPI

    from app.api.v1.stats.personal import router as personal_stats_router
    from app.db.base import get_db

    app = FastAPI()

    async def override_get_db():
        yield session

    app.include_router(personal_stats_router, prefix="/api/v1/stats/personal")
    app.dependency_overrides[get_db] = override_get_db

    return app


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    """Create async test client."""
    from httpx import ASGITransport, AsyncClient
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def sample_user(session):
    """Create a sample user for testing."""
    import uuid

    from app.db.models import User

    unique_id = str(uuid.uuid4())[:8]
    user = User(
        username=f"testuser{unique_id}",
        email=f"test{unique_id}@example.com",
        password_hash="hashed_password",
        department="研发一部",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


class TestPersonalCodeStats:
    """Test cases for GET /api/v1/stats/personal/code endpoint."""

    @pytest.mark.asyncio
    async def test_personal_code_stats_success(self, client: AsyncClient, sample_user):
        """Test getting personal code statistics."""
        response = await client.get(f"/api/v1/stats/personal/code?user_id={sample_user.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_commits" in data
        assert "total_prs" in data
        assert "lines_added" in data
        assert "lines_deleted" in data
        assert "avg_commits_per_day" in data

    @pytest.mark.asyncio
    async def test_personal_code_stats_with_date_range(self, client: AsyncClient, sample_user):
        """Test getting personal code stats with date range."""
        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()

        response = await client.get(
            f"/api/v1/stats/personal/code?user_id={sample_user.id}&start_date={start_date}&end_date={end_date}"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_commits" in data

    @pytest.mark.asyncio
    async def test_personal_code_stats_user_not_found(self, client: AsyncClient):
        """Test getting code stats for non-existent user."""
        response = await client.get("/api/v1/stats/personal/code?user_id=99999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_personal_code_stats_missing_user_id(self, client: AsyncClient):
        """Test getting code stats without user_id."""
        response = await client.get("/api/v1/stats/personal/code")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestPersonalTokenStats:
    """Test cases for GET /api/v1/stats/personal/token endpoint."""

    @pytest.mark.asyncio
    async def test_personal_token_stats_success(self, client: AsyncClient, sample_user):
        """Test getting personal token statistics."""
        response = await client.get(f"/api/v1/stats/personal/token?user_id={sample_user.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_tokens" in data
        assert "prompt_tokens" in data
        assert "completion_tokens" in data
        assert "avg_tokens_per_day" in data

    @pytest.mark.asyncio
    async def test_personal_token_stats_user_not_found(self, client: AsyncClient):
        """Test getting token stats for non-existent user."""
        response = await client.get("/api/v1/stats/personal/token?user_id=99999")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestPersonalBugRate:
    """Test cases for GET /api/v1/stats/personal/bug-rate endpoint."""

    @pytest.mark.asyncio
    async def test_personal_bug_rate_success(self, client: AsyncClient, sample_user):
        """Test getting personal bug rate statistics."""
        response = await client.get(f"/api/v1/stats/personal/bug-rate?user_id={sample_user.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_bugs" in data
        assert "critical_bugs" in data
        assert "bug_rate" in data
        assert "resolved_bugs" in data
        assert data["bug_rate"] >= 0

    @pytest.mark.asyncio
    async def test_personal_bug_rate_with_project(self, client: AsyncClient, sample_user, session):
        """Test getting personal bug rate for specific project."""
        import uuid

        from app.db.models import Project

        unique_id = str(uuid.uuid4())[:8]
        project = Project(
            name="测试项目",
            code=f"TEST{unique_id}",
            stage="研发",
            status="active",
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)

        response = await client.get(
            f"/api/v1/stats/personal/bug-rate?user_id={sample_user.id}&project_id={project.id}"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_bugs" in data

    @pytest.mark.asyncio
    async def test_personal_bug_rate_user_not_found(self, client: AsyncClient):
        """Test getting bug rate for non-existent user."""
        response = await client.get("/api/v1/stats/personal/bug-rate?user_id=99999")

        assert response.status_code == status.HTTP_404_NOT_FOUND
