from typing import Awaitable, Callable, Type

from app.schemas.pagination.pagination import (
    ModelType,
    PaginatedResponseBaseSchema,
    PaginationBaseSchema,
    ResponseType,
)


async def paginate_query(
    db_fetch_func: Callable[[int, int], Awaitable[tuple[list[ModelType], int]]],
    pagination: PaginationBaseSchema,
    response_schema: Type[PaginatedResponseBaseSchema[ResponseType]],
    item_schema: Type[ResponseType],
) -> PaginatedResponseBaseSchema[ResponseType]:
    """
    Execute pagination, fetch data, and return a unified paginated response.
    """

    skip = (pagination.page - 1) * pagination.limit
    items, total = await db_fetch_func(skip, pagination.limit)
    item_responses = [item_schema.model_validate(item) for item in items]
    total_pages = (
        (total + pagination.limit - 1) // pagination.limit
        if pagination.limit > 0
        else 1
    )

    return response_schema(
        total=total,
        page=pagination.page,
        limit=pagination.limit,
        total_pages=total_pages,
        results=item_responses,
    )
