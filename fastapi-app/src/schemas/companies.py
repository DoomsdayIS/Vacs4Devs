from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.choices import Companies


class CompanyBaseSchema(BaseModel):
    name: Companies
    description: str | None = None
    company_url: str | None = None
    company_vacs_url: str


class CompanyCreateSchema(CompanyBaseSchema):
    pass


class CompanyRetrieveSchema(CompanyBaseSchema):
    id: UUID
    created_at: datetime
    deleted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
