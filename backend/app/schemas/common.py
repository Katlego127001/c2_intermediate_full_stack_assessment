"""Shared schema helpers."""
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Generic paginated response envelope."""

    items: list[T]
    total: int
    page: int = Field(ge=1)
    size: int = Field(ge=1, le=200)
    pages: int


class Message(BaseModel):
    message: str
