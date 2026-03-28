"""Tests for FastAPI dependencies - TDD Red Phase."""

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient


class TestDatabaseDependency:
    """Test cases for database dependency."""

    @pytest.fixture
    def app(self):
        """Create test app with database dependency."""
        from app.core.dependencies import get_db

        app = FastAPI()

        @app.get("/test/db")
        async def test_db(db=Depends(get_db)):
            return {"db_type": type(db).__name__}

        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    @pytest.mark.asyncio
    async def test_get_db_yields_session(self):
        """Test get_db yields an async session."""
        from sqlalchemy.ext.asyncio import AsyncSession

        from app.core.dependencies import get_db

        # Get the generator
        db_gen = get_db()
        db = await db_gen.__anext__()

        assert isinstance(db, AsyncSession)

        # Clean up
        try:
            await db_gen.__anext__()
        except StopAsyncIteration:
            pass


class TestCurrentUserDependency:
    """Test cases for current user dependency."""

    def test_get_current_user_exists(self):
        """Test get_current_user dependency exists."""
        from app.core.dependencies import get_current_user

        assert callable(get_current_user)

    def test_get_current_active_user_exists(self):
        """Test get_current_active_user dependency exists."""
        from app.core.dependencies import get_current_active_user

        assert callable(get_current_active_user)


class TestPermissionDependencies:
    """Test cases for permission dependencies."""

    def test_require_permission_exists(self):
        """Test require_permission dependency factory exists."""
        from app.core.dependencies import require_permission

        assert callable(require_permission)

    def test_require_permission_creates_dependency(self):
        """Test require_permission creates a dependency."""
        from app.core.dependencies import require_permission

        # Create a permission dependency
        require_admin = require_permission("admin")
        assert callable(require_admin)


class TestCommonParameters:
    """Test cases for common query parameters."""

    def test_common_parameters_exists(self):
        """Test CommonQueryParams class exists."""
        from app.core.dependencies import CommonQueryParams

        params = CommonQueryParams()
        assert hasattr(params, "skip")
        assert hasattr(params, "limit")

    def test_common_parameters_defaults(self):
        """Test CommonQueryParams has correct defaults."""
        from app.core.dependencies import CommonQueryParams

        params = CommonQueryParams()
        assert params.skip == 0
        assert params.limit == 100

    def test_common_parameters_custom_values(self):
        """Test CommonQueryParams accepts custom values."""
        from app.core.dependencies import CommonQueryParams

        params = CommonQueryParams(skip=10, limit=50)
        assert params.skip == 10
        assert params.limit == 50
