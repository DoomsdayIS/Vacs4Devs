from sqlalchemy import select, func, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from src.choices import Languages, Grades
from src.models import Vacancy, Company
from src.schemas import VacancyCreateSchema, VacancyRetrieveSchema
from src.schemas.vacancies import VacanciesGeneralInfoSchema


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


async def get_general_info(
    session: AsyncSession,
    lang: Languages | None,
    grade: Grades | None,
    min_experience: int,
    max_experience: int,
) -> VacanciesGeneralInfoSchema:
    suit_vacancies = select(Vacancy).where(
        Vacancy.experience >= min_experience, Vacancy.experience <= max_experience
    )
    if lang:
        suit_vacancies = suit_vacancies.filter(Vacancy.lang == lang)
    if grade:
        suit_vacancies = suit_vacancies.filter(Vacancy.grade == grade)
    suit_vacancies = suit_vacancies.join(
        Vacancy.company.and_(
            Company.deleted_at.is_(None),
        )
    ).subquery()

    result = {}

    all_time_vacs_stmt = select(func.count(Vacancy.id)).join(
        suit_vacancies, Vacancy.id == suit_vacancies.c.id
    )
    all_time_vacs_cnt = await session.scalars(all_time_vacs_stmt)
    result["all"] = all_time_vacs_cnt.all()[0]

    active_vacs_stmt = (
        select(func.count(Vacancy.id))
        .where(Vacancy.deleted_at.is_(None))
        .join(suit_vacancies, Vacancy.id == suit_vacancies.c.id)
    )
    active_vacs_cnt = await session.scalars(active_vacs_stmt)
    result["active"] = active_vacs_cnt.all()[0]

    if not lang:
        vacs_lang_distribution_stmt = (
            select(Vacancy.lang, func.count(Vacancy.lang).label("lang_cnt"))
            .join(suit_vacancies, Vacancy.id == suit_vacancies.c.id)
            .group_by(Vacancy.lang)
        )
        vacs_lang_distribution = await session.execute(vacs_lang_distribution_stmt)
        lang_dict = {}
        for lang_distribution in vacs_lang_distribution:
            lang_dict[lang_distribution[0]] = lang_distribution[1]
        result["lang_distribution"] = lang_dict if lang_dict else None

    if not grade:
        vacs_grade_distribution_stmt = (
            select(Vacancy.grade, func.count(Vacancy.grade).label("grade_cnt"))
            .join(suit_vacancies, Vacancy.id == suit_vacancies.c.id)
            .group_by(Vacancy.grade)
        )
        vacs_grade_distribution = await session.execute(vacs_grade_distribution_stmt)
        grade_dict = {}
        for grade_distribution in vacs_grade_distribution:
            grade_dict[grade_distribution[0]] = grade_distribution[1]
        result["grade_distribution"] = grade_dict if grade_dict else None

    vacs_comp_distribution_stmt = (
        select(Company.name, func.count(Company.name).label("company_cnt"))
        .join(Vacancy, Company.id == Vacancy.company_id)
        .join(suit_vacancies, Vacancy.id == suit_vacancies.c.id)
        .group_by(Company.name)
    )
    vacs_comp_distribution = await session.execute(vacs_comp_distribution_stmt)
    comp_dict = {}
    for comp_distribution in vacs_comp_distribution:
        comp_dict[comp_distribution[0]] = comp_distribution[1]
    result["company_distribution"] = comp_dict if comp_dict else None

    avg_vacancy_lifetime_stmt = (
        select(
            func.avg(cast(Vacancy.deleted_at, Date) - cast(Vacancy.created_at, Date))
        )
        .join(suit_vacancies, Vacancy.id == suit_vacancies.c.id)
        .where(Vacancy.deleted_at.isnot(None))
    )
    avg_vacancy_lifetime = await session.scalars(avg_vacancy_lifetime_stmt)
    lifetime = avg_vacancy_lifetime.all()
    if lifetime[0]:
        result["avg_vacancy_lifetime"] = round(lifetime[0], 3)
    return VacanciesGeneralInfoSchema(**result)


async def get_time_trend(
    session: AsyncSession,
    lang: Languages | None,
    grade: Grades | None,
    min_experience: int,
    max_experience: int,
    trend_size: int,
) -> dict[str, int]:
    suit_vacancies = select(Vacancy).where(
        Vacancy.experience >= min_experience, Vacancy.experience <= max_experience
    )
    if lang:
        suit_vacancies = suit_vacancies.filter(Vacancy.lang == lang)
    if grade:
        suit_vacancies = suit_vacancies.filter(Vacancy.grade == grade)
    suit_vacancies = suit_vacancies.subquery()

    time_trend_stmt = (
        select(
            cast(Vacancy.created_at, Date), func.count(cast(Vacancy.created_at, Date))
        )
        .join(suit_vacancies, Vacancy.id == suit_vacancies.c.id)
        .where(cast(Vacancy.created_at, Date) + trend_size > cast(func.now(), Date))
        .group_by(cast(Vacancy.created_at, Date))
    )
    time_trend = await session.execute(time_trend_stmt)
    result = {}
    for date_cnt in time_trend:
        result[date_cnt[0].isoformat()] = date_cnt[1]
    return result
