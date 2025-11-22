from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.pagination import PaginatedResponseBaseSchema


class CompanyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)


class CompanyUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, min_length=1)
    is_visible: bool | None = None


class CompanyResponse(BaseModel):
    id: int
    name: str
    description: str
    is_visible: bool
    owner_id: int
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class CompaniesListResponse(PaginatedResponseBaseSchema[CompanyResponse]):
    """Unified paginated response for companies."""

    pass
