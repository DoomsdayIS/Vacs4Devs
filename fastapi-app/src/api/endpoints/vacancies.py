from typing import Annotated

from fastapi import Depends, Query, APIRouter
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.choices import Languages, Grades, TimeTrendMode
from src.database import get_async_session
from src.db_crud import vacancies as crud_vacancies
from src.schemas.vacancies import (
    VacancyWithCompanyNameSchema,
    VacanciesGeneralInfoSchema,
)

router = APIRouter()
CurrentSession = Annotated[AsyncSession, Depends(get_async_session)]


class FilterParams(BaseModel):
    lang: Languages | None = None
    grade: Grades | None = None
    min_experience: int = 0
    max_experience: int = 100


@router.get("/all", response_model=list[VacancyWithCompanyNameSchema])
async def get_active_vacancies(
    session: CurrentSession, filter_query: Annotated[FilterParams, Query()]
):
    vacancies = await crud_vacancies.get_vacancies(
        session=session,
        lang=filter_query.lang,
        grade=filter_query.grade,
        min_experience=filter_query.min_experience,
        max_experience=filter_query.max_experience,
        deleted=False,
        with_company_name=True,
    )
    response = []
    for vacancy in vacancies:
        response.append(
            VacancyWithCompanyNameSchema(
                **vacancy.Vacancy.to_dict(), company_name=vacancy.company_name
            )
        )
    return response


@router.get("/general-ifo", response_model=VacanciesGeneralInfoSchema)
async def get_general_info_about_vacancies(
    session: CurrentSession, filter_query: Annotated[FilterParams, Query()]
) -> VacanciesGeneralInfoSchema:
    result = await crud_vacancies.get_general_info(
        session=session,
        lang=filter_query.lang,
        grade=filter_query.grade,
        min_experience=filter_query.min_experience,
        max_experience=filter_query.max_experience,
    )
    return result


class TimeTrendFilterParams(FilterParams):
    mode: TimeTrendMode


@router.get("/time-trend")
async def get_time_trend__for_new_vacancies(
    session: CurrentSession,
    filter_query: Annotated[TimeTrendFilterParams, Query()],
) -> dict[str, int]:
    return await crud_vacancies.get_time_trend(
        session=session,
        lang=filter_query.lang,
        grade=filter_query.grade,
        min_experience=filter_query.min_experience,
        max_experience=filter_query.max_experience,
        trend_size=int(filter_query.mode.value),
    )
