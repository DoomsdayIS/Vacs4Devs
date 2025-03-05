from typing import Annotated

from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.db_crud import vacancies as crud_vacancies
from src.schemas import VacancyRetrieveSchema, VacancyCreateSchema

router = APIRouter()
CurrentSession = Annotated[AsyncSession, Depends(get_async_session)]


@router.get("/test1", response_model=list[VacancyRetrieveSchema])
async def get_vacancies(session: CurrentSession):
    vacancies = await crud_vacancies.get_vacancies(session=session)
    return vacancies


@router.post("/test2", response_model=VacancyRetrieveSchema)
async def create_vacancy(session: CurrentSession, vacancy: VacancyCreateSchema):
    vacancy = await crud_vacancies.create_vacancy(
        session=session, vacancy_create=vacancy
    )
    return vacancy
