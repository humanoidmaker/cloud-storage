from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class SortParams(BaseModel):
    sort_by: str = "created_at"
    sort_order: str = "desc"  # asc or desc


class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None


class SuccessResponse(BaseModel):
    message: str
    data: dict[str, Any] | None = None


def calculate_total_pages(total: int, page_size: int) -> int:
    if total == 0 or page_size == 0:
        return 0
    return (total + page_size - 1) // page_size
