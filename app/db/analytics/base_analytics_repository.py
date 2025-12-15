from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import FunctionElement


class week_trunc(FunctionElement):
    """
    SQLAlchemy expression to truncate date to week start (Monday).
    Automatically adapts for PostgreSQL and SQLite dialects.

    Usage: week_trunc(MyTable.created_at)
    """

    name = "week_trunc"
    inherit_cache = True

    def __init__(self, expr):
        super(week_trunc, self).__init__(expr)


@compiles(week_trunc, "postgresql")
def compile_postgres(element, compiler, **kw):
    """Compiles to DATE_TRUNC('week', ...) for PostgreSQL."""
    date_column = compiler.process(element.clauses.clauses[0])
    return f"DATE_TRUNC('week', {date_column})"


@compiles(week_trunc, "sqlite")
def compile_sqlite(element, compiler, **kw):
    """Compiles to DATE(...) calculation for SQLite."""
    date_column = compiler.process(element.clauses.clauses[0])
    return f"DATE({date_column}, 'weekday 1', '-7 days')"


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

    @staticmethod
    def week_trunc(column):
        """Returns week start (Monday) for the given date column."""
        return week_trunc(column)

    async def count_from_subquery(self, stmt) -> int:
        """
        Count total rows for a grouped query using subquery.
        """
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self.session.execute(count_stmt)
        return result.scalar_one()
