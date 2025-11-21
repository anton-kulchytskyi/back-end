from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums.role import Role


class CompanyMemberResponse(BaseModel):
    """Company member response schema."""

    id: int
    company_id: int
    user_id: int
    role: Role
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class CompanyMembersListResponse(BaseModel):
    """Paginated list of company members."""

    members: list[CompanyMemberResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
