from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")
ResponseType = TypeVar("ResponseType", bound=BaseModel)
ModelType = TypeVar("ModelType", bound=Any)


class PaginationBaseSchema(BaseModel):
    page: int = Field(1, ge=1, description="Page number (must be 1 or greater)")
    limit: int = Field(10, ge=1, description="Limit (must be 1 or greater)")


class PaginatedResponseBaseSchema(BaseModel, Generic[T]):
    total: int
    page: int
    limit: int
    total_pages: int
    results: list[T]
