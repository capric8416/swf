"""Common schemas for API responses."""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Generic API response wrapper.

    All API responses should use this format for consistency.
    """

    code: int = 200
    message: str = "success"
    data: T | None = None


class ErrorResponse(BaseModel):
    """Error response schema."""

    code: int
    message: str
    detail: str | None = None
