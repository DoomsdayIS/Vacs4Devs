from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.choices import Languages, Grades


class SubscriberBaseSchema(BaseModel):
    name: str
    email: str
    lang: Languages
    grade: Grades | None


class SubscriberCreateSchema(SubscriberBaseSchema):
    pass


class SubscriberUpdateSchema(BaseModel):
    lang: Languages | None
    grade: Grades | None


class SubscriberRetrieveSchema(SubscriberBaseSchema):
    id: UUID
    created_at: datetime
    deleted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
