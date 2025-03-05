from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Vacancy
from src.schemas import VacancyCreateSchema


async def get_vacancies(session: AsyncSession) -> Sequence[Vacancy]:
    stmt = select(Vacancy).order_by(Vacancy.created_at)
    result = await session.scalars(stmt)
    return result.all()


async def create_vacancy(
    session: AsyncSession, vacancy_create: VacancyCreateSchema
) -> Vacancy:
    vacancy = Vacancy(**vacancy_create.model_dump())
    session.add(vacancy)
    await session.commit()
    await session.refresh(vacancy)
    return vacancy


async def create_companies(
    session: AsyncSession, vacancies: list[VacancyCreateSchema]
) -> list[Vacancy]:
    objs = []
    for vac in vacancies:
        db_obj = Vacancy(**vac.model_dump())
        objs.append(db_obj)
    session.add_all(objs)
    await session.commit()
    for db_obj in objs:
        await session.refresh(db_obj)
    return objs
