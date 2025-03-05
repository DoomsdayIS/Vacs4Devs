from typing import Annotated

from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.choices import Languages, Grades
from src.database import get_async_session
from src.db_crud import vacancies as crud_vacancies
from src.schemas.vacancies import VacancyWithCompanyNameSchema

router = APIRouter()
CurrentSession = Annotated[AsyncSession, Depends(get_async_session)]


@router.get("/all", response_model=list[VacancyWithCompanyNameSchema])
async def get_vacancies(
    session: CurrentSession,
    lang: Languages | None = None,
    grade: Grades | None = None,
    min_experience: int = 0,
    max_experience: int = 100,
):
    vacancies = await crud_vacancies.get_vacancies(
        session=session,
        lang=lang,
        grade=grade,
        min_experience=min_experience,
        max_experience=max_experience,
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


# @router.get("/test3")
# async def get_vacancies(session: CurrentSession):
#     await daily_vacancy_processing(session)
#     return {}
