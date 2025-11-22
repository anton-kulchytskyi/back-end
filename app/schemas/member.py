from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums.role import Role
from app.schemas.pagination import PaginatedResponseBaseSchema


class CompanyMemberResponse(BaseModel):
    """Company member response schema."""

    id: int
    company_id: int
    user_id: int
    role: Role
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class CompanyMembersListResponse(PaginatedResponseBaseSchema[CompanyMemberResponse]):
    """Unified paginated response for company members."""

    pass  # All fields inherited from pagination
