from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.choices import Languages, Grades
from src.models import Vacancy, Company
from src.schemas import VacancyCreateSchema, VacancyRetrieveSchema


async def get_vacancies(
    session: AsyncSession,
    deleted: bool,
    lang: Languages | None,
    grade: Grades | None,
    min_experience: int,
    max_experience: int,
    with_company_name: bool = False,
):
    stmt = (
        select(Vacancy)
        .where(
            Vacancy.experience >= min_experience, Vacancy.experience <= max_experience
        )
        .order_by(Vacancy.created_at)
    )
    if not deleted:
        stmt = stmt.filter(Vacancy.deleted_at.is_(None))
    if lang:
        stmt = stmt.filter(Vacancy.lang == lang)
    if grade:
        stmt = stmt.filter(Vacancy.grade == grade)
    if with_company_name:
        stmt = stmt.join(
            Vacancy.company.and_(
                Company.deleted_at.is_(None),
            )
        )
        stmt = stmt.add_columns(Company.name.label("company_name"))

    result = await session.execute(stmt)
    return result.all()


async def create_vacancy(
    session: AsyncSession, vacancy_create: VacancyCreateSchema
) -> Vacancy:
    vacancy = Vacancy(**vacancy_create.model_dump())
    session.add(vacancy)
    await session.commit()
    await session.refresh(vacancy)
    return vacancy


async def create_vacancies(
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


async def update_vacancies(
    session: AsyncSession, in_objs: dict[Vacancy, VacancyRetrieveSchema]
) -> list[Vacancy]:
    for obj, in_obj in in_objs.items():
        update_data = in_obj.model_dump()
        for field in update_data:
            setattr(obj, field, update_data[field])
        session.add(obj)
    await session.commit()
    updated_objs = list(in_objs.keys())
    for updated_obj in updated_objs:
        await session.refresh(updated_obj)
    return updated_objs
