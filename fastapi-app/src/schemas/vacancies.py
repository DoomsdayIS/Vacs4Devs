from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic import ConfigDict

from src.choices import Languages, Grades, Companies


class VacancyBaseSchema(BaseModel):
    title: str
    grade: Grades
    lang: Languages
    experience: int = Field(ge=0)
    link: str
    company_id: UUID


class VacancyCreateSchema(VacancyBaseSchema):
    pass


class VacancyRetrieveSchema(VacancyBaseSchema):
    id: UUID
    created_at: datetime
    deleted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class VacancyWithCompanyNameSchema(VacancyRetrieveSchema):
    company_name: Companies


class VacanciesGeneralInfoSchema(BaseModel):
    all: int = Field(ge=0)
    active: int = Field(ge=0)
    lang_distribution: dict[Languages, int] | None = None
    company_distribution: dict[Companies, int] | None = None
    grade_distribution: dict[Grades, int] | None = None
    avg_vacancy_lifetime: float | None = None
