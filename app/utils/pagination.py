from typing import Awaitable, Callable, Type

from app.schemas.pagination import (
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

    Args:
        db_fetch_func: Async function that receives (skip, limit)
                       and returns a tuple (items, total_count).
        pagination: Pagination parameters (page, limit).
        response_schema: Final paginated response schema (e.g., UsersListResponse).
        item_schema: Schema used to serialize each item (e.g., UserDetailResponse).

    Returns:
        A paginated response object containing:
        - total number of items
        - current page
        - limit per page
        - total pages
        - list of serialized results
    """

    # 1. Calculate offset (skip)
    skip = (pagination.page - 1) * pagination.limit

    # 2. Fetch data with pagination from the database
    items, total = await db_fetch_func(skip, pagination.limit)

    # 3. Convert ORM items into Pydantic response schemas
    item_responses = [item_schema.model_validate(item) for item in items]

    # 4. Calculate total pages
    total_pages = (
        (total + pagination.limit - 1) // pagination.limit
        if pagination.limit > 0
        else 1
    )

    # 5. Return a unified paginated response
    return response_schema(
        total=total,
        page=pagination.page,
        limit=pagination.limit,
        total_pages=total_pages,
        results=item_responses,
    )
