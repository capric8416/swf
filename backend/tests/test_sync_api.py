"""Tests for Sync API - TDD Red Phase.

These tests define the expected behavior of the data synchronization API endpoints.
"""


import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient


@pytest.fixture
def app(session) -> FastAPI:
    """Create test FastAPI app with routes and overridden dependencies."""
    from fastapi import FastAPI

    from app.api.v1.sync import router as sync_router
    from app.db.base import get_db

    app = FastAPI()

    async def override_get_db():
        yield session

    app.include_router(sync_router, prefix="/api/v1/sync")
    app.dependency_overrides[get_db] = override_get_db

    return app


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    """Create async test client."""
    from httpx import ASGITransport, AsyncClient
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestSyncGitLab:
    """Test cases for POST /api/v1/sync/gitlab endpoint."""

    @pytest.mark.asyncio
    async def test_sync_gitlab_success(self, client: AsyncClient):
        """Test triggering GitLab sync."""
        sync_data = {
            "project_ids": [1, 2, 3],
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
        }

        response = await client.post("/api/v1/sync/gitlab", json=sync_data)

        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "pending"
        assert data["source"] == "gitlab"

    @pytest.mark.asyncio
    async def test_sync_gitlab_empty_body(self, client: AsyncClient):
        """Test triggering GitLab sync with empty body (sync all)."""
        response = await client.post("/api/v1/sync/gitlab", json={})

        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "pending"


class TestSyncTrae:
    """Test cases for POST /api/v1/sync/trae endpoint."""

    @pytest.mark.asyncio
    async def test_sync_trae_success(self, client: AsyncClient):
        """Test triggering Trae sync."""
        sync_data = {
            "user_ids": [1, 2],
            "start_date": "2024-01-01",
        }

        response = await client.post("/api/v1/sync/trae", json=sync_data)

        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "pending"
        assert data["source"] == "trae"


class TestSyncZendao:
    """Test cases for POST /api/v1/sync/zendao endpoint."""

    @pytest.mark.asyncio
    async def test_sync_zendao_success(self, client: AsyncClient):
        """Test triggering Zendao sync."""
        sync_data = {
            "project_ids": [1],
        }

        response = await client.post("/api/v1/sync/zendao", json=sync_data)

        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "pending"
        assert data["source"] == "zendao"


class TestSyncTasks:
    """Test cases for GET /api/v1/sync/tasks endpoint."""

    @pytest.mark.asyncio
    async def test_list_sync_tasks(self, client: AsyncClient):
        """Test listing sync tasks."""
        response = await client.get("/api/v1/sync/tasks")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_list_sync_tasks_with_filter(self, client: AsyncClient):
        """Test listing sync tasks with filter."""
        response = await client.get("/api/v1/sync/tasks?status=pending&source=gitlab")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data["items"], list)
        # All returned items should match the filter
        for item in data["items"]:
            assert item["status"] == "pending"
            assert item["source"] == "gitlab"

    @pytest.mark.asyncio
    async def test_list_sync_tasks_pagination(self, client: AsyncClient):
        """Test sync tasks pagination."""
        response = await client.get("/api/v1/sync/tasks?page=1&page_size=5")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5


class TestSyncLogs:
    """Test cases for GET /api/v1/sync/logs endpoint."""

    @pytest.mark.asyncio
    async def test_list_sync_logs(self, client: AsyncClient):
        """Test listing sync logs."""
        response = await client.get("/api/v1/sync/logs")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_list_sync_logs_with_task_id(self, client: AsyncClient):
        """Test listing sync logs for specific task."""
        response = await client.get("/api/v1/sync/logs?task_id=test-task-id")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data["items"], list)
        # All returned items should have the specified task_id
        for item in data["items"]:
            assert item["task_id"] == "test-task-id"

    @pytest.mark.asyncio
    async def test_list_sync_logs_with_level(self, client: AsyncClient):
        """Test listing sync logs with level filter."""
        response = await client.get("/api/v1/sync/logs?level=error")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data["items"], list)
        # All returned items should have level >= error
        for item in data["items"]:
            assert item["level"] in ["error", "critical"]
