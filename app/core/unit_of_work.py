from abc import ABC, abstractmethod

from app.core.database import AsyncSessionLocal
from app.db import (
    CompanyMemberRepository,
    CompanyRepository,
    InvitationRepository,
    RequestRepository,
    UserRepository,
)


class AbstractUnitOfWork(ABC):
    company_member: CompanyMemberRepository
    companies: CompanyRepository
    invitations: InvitationRepository
    requests: RequestRepository
    users: UserRepository

    @abstractmethod
    async def __aenter__(self):
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(self):
        raise NotImplementedError

    @abstractmethod
    async def commit(self):
        raise NotImplementedError

    @abstractmethod
    async def rollback(self):
        raise NotImplementedError


class SQLAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        self.session_factory = AsyncSessionLocal

    async def __aenter__(self):
        self.session = self.session_factory()

        self.company_member = CompanyMemberRepository(session=self.session)
        self.companies = CompanyRepository(session=self.session)
        self.invitations = InvitationRepository(session=self.session)
        self.requests = RequestRepository(session=self.session)
        self.users = UserRepository(session=self.session)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.rollback()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
