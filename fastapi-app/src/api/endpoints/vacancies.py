from typing import Annotated

from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.db_crud import vacancies as crud_vacancies
from src.parsers import (
    AviasalesVacancyParser,
    CompanyVacanciesParser,
    SelectelVacancyParser,
    X5VacancyParser,
)
from src.schemas import VacancyRetrieveSchema, VacancyCreateSchema

router = APIRouter()
CurrentSession = Annotated[AsyncSession, Depends(get_async_session)]


@router.get("/test1", response_model=list[VacancyRetrieveSchema])
async def get_vacancies(session: CurrentSession):
    print(type(AviasalesVacancyParser))
    print(type(CompanyVacanciesParser))
    vacancies = await crud_vacancies.get_vacancies(session=session)
    return vacancies


@router.post("/test2", response_model=VacancyRetrieveSchema)
async def create_vacancy(session: CurrentSession, vacancy: VacancyCreateSchema):
    vacancy = await crud_vacancies.create_vacancy(
        session=session, vacancy_create=vacancy
    )
    return vacancy


@router.get("/test3")
async def get_vacancies(session: CurrentSession):
    vls = await X5VacancyParser.get_all_actual_vacancy_links()
    for i in vls:
        print(i.link_text)
    res = await vls[-1].parser_class.vacancy_schema_from_vacancy_link(vls[-1].link_text)
    vacancy = await crud_vacancies.create_vacancy(session=session, vacancy_create=res)
    print(res)
    return {}
