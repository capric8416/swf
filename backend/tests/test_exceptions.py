"""Tests for exception handling - TDD Red Phase."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestCustomExceptions:
    """Test cases for custom exceptions."""

    def test_app_exception_exists(self):
        """Test that AppException class exists."""
        from app.core.exceptions import AppException

        exc = AppException(message="Test error")
        assert exc.message == "Test error"
        assert exc.status_code == 500

    def test_not_found_exception(self):
        """Test NotFoundException."""
        from app.core.exceptions import NotFoundException

        exc = NotFoundException(resource="User", identifier="123")
        assert exc.message == "User with id 123 not found"
        assert exc.status_code == 404

    def test_validation_exception(self):
        """Test ValidationException."""
        from app.core.exceptions import ValidationException

        exc = ValidationException(field="email", message="Invalid email format")
        assert exc.message == "Invalid email format"
        assert exc.status_code == 422

    def test_auth_exception(self):
        """Test AuthenticationException."""
        from app.core.exceptions import AuthenticationException

        exc = AuthenticationException(message="Invalid credentials")
        assert exc.message == "Invalid credentials"
        assert exc.status_code == 401

    def test_permission_exception(self):
        """Test PermissionDeniedException."""
        from app.core.exceptions import PermissionDeniedException

        exc = PermissionDeniedException(permission="user:manage")
        assert "user:manage" in exc.message
        assert exc.status_code == 403


class TestExceptionHandlers:
    """Test exception handlers."""

    @pytest.fixture
    def app(self):
        """Create test app with exception handlers."""
        from app.core.exceptions import (
            AppException,
            AuthenticationException,
            NotFoundException,
            PermissionDeniedException,
            ValidationException,
            app_exception_handler,
            auth_handler,
            not_found_handler,
            permission_handler,
            validation_handler,
        )

        app = FastAPI()

        # Register handlers
        app.add_exception_handler(AppException, app_exception_handler)
        app.add_exception_handler(NotFoundException, not_found_handler)
        app.add_exception_handler(ValidationException, validation_handler)
        app.add_exception_handler(AuthenticationException, auth_handler)
        app.add_exception_handler(PermissionDeniedException, permission_handler)

        @app.get("/test/app-error")
        def raise_app_error():
            raise AppException(message="App error occurred")

        @app.get("/test/not-found")
        def raise_not_found():
            raise NotFoundException(resource="User", identifier="999")

        @app.get("/test/validation")
        def raise_validation():
            raise ValidationException(field="email", message="Invalid email")

        @app.get("/test/auth")
        def raise_auth():
            raise AuthenticationException(message="Not authenticated")

        @app.get("/test/permission")
        def raise_permission():
            raise PermissionDeniedException(permission="admin")

        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_app_exception_response(self, client):
        """Test app exception returns correct response."""
        response = client.get("/test/app-error")

        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == "INTERNAL_ERROR"
        assert data["error"]["message"] == "App error occurred"

    def test_not_found_response(self, client):
        """Test not found returns 404."""
        response = client.get("/test/not-found")

        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "NOT_FOUND"
        assert "User" in data["error"]["message"]

    def test_validation_response(self, client):
        """Test validation returns 422."""
        response = client.get("/test/validation")

        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert data["error"]["details"]["field"] == "email"

    def test_auth_response(self, client):
        """Test auth exception returns 401."""
        response = client.get("/test/auth")

        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"

    def test_permission_response(self, client):
        """Test permission exception returns 403."""
        response = client.get("/test/permission")

        assert response.status_code == 403
        data = response.json()
        assert data["error"]["code"] == "PERMISSION_DENIED"
