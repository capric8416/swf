"""Custom exceptions and exception handlers for the application.

TDD Green Phase: Implement exceptions to make tests pass.
"""

from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(AppException):
    """Resource not found exception."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} with id {identifier} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            details={"resource": resource, "identifier": identifier},
        )


class ValidationException(AppException):
    """Validation error exception."""

    def __init__(self, field: str, message: str):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            details={"field": field},
        )


class AuthenticationException(AppException):
    """Authentication error exception."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTHENTICATION_ERROR",
        )


class PermissionDeniedException(AppException):
    """Permission denied exception."""

    def __init__(self, permission: str):
        super().__init__(
            message=f"Permission denied: {permission}",
            status_code=status.HTTP_403_FORBIDDEN,
            code="PERMISSION_DENIED",
            details={"permission": permission},
        )


# Exception handlers
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle AppException."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


async def not_found_handler(request: Request, exc: NotFoundException) -> JSONResponse:
    """Handle NotFoundException."""
    return await app_exception_handler(request, exc)


async def validation_handler(request: Request, exc: ValidationException) -> JSONResponse:
    """Handle ValidationException."""
    return await app_exception_handler(request, exc)


async def auth_handler(request: Request, exc: AuthenticationException) -> JSONResponse:
    """Handle AuthenticationException."""
    return await app_exception_handler(request, exc)


async def permission_handler(request: Request, exc: PermissionDeniedException) -> JSONResponse:
    """Handle PermissionDeniedException."""
    return await app_exception_handler(request, exc)


# Register all exception handlers
def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI app."""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(NotFoundException, not_found_handler)
    app.add_exception_handler(ValidationException, validation_handler)
    app.add_exception_handler(AuthenticationException, auth_handler)
    app.add_exception_handler(PermissionDeniedException, permission_handler)
