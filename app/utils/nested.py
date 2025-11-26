from typing import Any, Callable, Iterable

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession


async def replace_children(
    session: AsyncSession,
    child_model: Any,
    parent_id_field: Any,
    parent_id: int,
    new_children_data: Iterable[Any],
    create_child_func: Callable[[Any], Any],
):
    """
    Universal nested collection replace operation:
    1. Delete all existing children by parent_id
    2. Create new children using builder function
    """
    await session.execute(delete(child_model).where(parent_id_field == parent_id))

    created = []
    for child_data in new_children_data:
        obj = create_child_func(child_data)
        session.add(obj)
        created.append(obj)

    await session.flush()
    return created
