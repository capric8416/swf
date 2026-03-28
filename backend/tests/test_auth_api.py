"""Tests for authentication API endpoints.

TDD Red Phase: Write tests before implementation.
"""

from datetime import UTC

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import create_access_token, get_password_hash
from app.db.models import User
from app.main import app


@pytest.fixture
async def client(session: AsyncSession):
    """Create an async test client with overridden database dependency."""
    # Override the get_db dependency to use the test session
    async def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clean up overrides after test
    app.dependency_overrides.clear()


class TestLoginEndpoint:
    """Tests for POST /api/v1/auth/login endpoint."""

    async def test_login_with_valid_credentials(self, client: AsyncClient, session: AsyncSession):
        """Test login with valid credentials returns tokens."""
        # Create test user
        user = User(
            username="api_login_user",
            email="api_login@example.com",
            password_hash=get_password_hash("testpass123"),
            department="IT",
            is_active=True,
        )
        session.add(user)
        await session.commit()

        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "api_login_user", "password": "testpass123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_with_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials returns 401."""
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "wronguser", "password": "wrongpass"},
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    async def test_login_with_missing_username(self, client: AsyncClient):
        """Test login with missing username returns 422."""
        response = await client.post(
            "/api/v1/auth/login",
            data={"password": "testpass123"},
        )

        assert response.status_code == 422

    async def test_login_with_missing_password(self, client: AsyncClient):
        """Test login with missing password returns 422."""
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "testuser"},
        )

        assert response.status_code == 422


class TestRefreshEndpoint:
    """Tests for POST /api/v1/auth/refresh endpoint."""

    async def test_refresh_with_valid_token(self, client: AsyncClient, session: AsyncSession):
        """Test refresh with valid refresh token returns new access token."""
        # Create test user
        user = User(
            username="api_refresh_user",
            email="api_refresh@example.com",
            password_hash=get_password_hash("testpass123"),
            department="IT",
            is_active=True,
        )
        session.add(user)
        await session.commit()

        from app.core.security import create_refresh_token
        refresh_token = create_refresh_token({"sub": str(user.id)})

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_refresh_with_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token returns 401."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    async def test_refresh_with_missing_token(self, client: AsyncClient):
        """Test refresh with missing token returns 422."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={},
        )

        assert response.status_code == 422


class TestMeEndpoint:
    """Tests for GET /api/v1/auth/me endpoint."""

    async def test_get_current_user_with_valid_token(self, client: AsyncClient, session: AsyncSession):
        """Test getting current user with valid token returns user info."""
        # Create test user
        user = User(
            username="api_me_user",
            email="api_me@example.com",
            password_hash=get_password_hash("testpass123"),
            department="IT",
            is_active=True,
        )
        session.add(user)
        await session.commit()

        token = create_access_token({"sub": str(user.id), "username": user.username})

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user.id
        assert data["username"] == user.username
        assert data["email"] == user.email
        assert "password_hash" not in data

    async def test_get_current_user_without_token(self, client: AsyncClient):
        """Test getting current user without token returns 401."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401

    async def test_get_current_user_with_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token returns 401."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401

    async def test_get_current_user_with_expired_token(self, client: AsyncClient):
        """Test getting current user with expired token returns 401."""
        from datetime import datetime, timedelta

        from jose import jwt

        from app.core.config import settings

        # Create an expired token manually
        expire = datetime.now(UTC) - timedelta(minutes=1)
        data = {"sub": "1", "username": "testuser", "exp": expire}
        expired_token = jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        assert response.status_code == 401
