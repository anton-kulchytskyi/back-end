from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseAnalyticsRepository:
    """
    Base helper for analytics repositories.
    Contains reusable SQL expressions and helpers.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def avg_correct_case(column):
        """
        AVG(CASE WHEN column IS TRUE THEN 1 ELSE 0 END)
        """
        return func.avg(case((column.is_(True), 1), else_=0))

    async def count_from_subquery(self, stmt) -> int:
        """
        Count total rows for a grouped query using subquery.
        """
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self.session.execute(count_stmt)
        return result.scalar_one()
