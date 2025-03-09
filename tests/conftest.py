from random import randint

import pytest_asyncio

from src.choices import Companies, Languages, Grades
from src.config import settings
from src.database import sessionmanager
from src.db_crud.companies import create_companies, get_all_companies
from src.db_crud.vacancies import create_vacancies
from src.models import Base
from src.schemas import CompanyCreateSchema, VacancyCreateSchema


@pytest_asyncio.fixture(scope="session", autouse=True, loop_scope="session")
async def setup_db():
    assert settings.POSTGRES_DB == "test"
    sessionmanager.init(settings.SQLALCHEMY_DATABASE_URL.unicode_string())
    yield
    await sessionmanager.close()


@pytest_asyncio.fixture(scope="function", loop_scope="session")
async def create_tables():
    async with sessionmanager.connect() as connection:
        await sessionmanager.drop_all(connection, Base.metadata)
        await sessionmanager.create_all(connection, Base.metadata)


@pytest_asyncio.fixture(scope="function", loop_scope="session")
async def fill_companies_table(create_tables):
    async with sessionmanager.session() as session:
        ccs_list = []
        for company_name in Companies:
            ccs = CompanyCreateSchema(
                name=company_name, company_vacs_url=company_name + "_url"
            )
            ccs_list.append(ccs)
        await create_companies(session, ccs_list)


@pytest_asyncio.fixture(scope="function", loop_scope="session")
async def fill_vacancies_table(fill_companies_table):
    async with sessionmanager.session() as session:
        all_companies = await get_all_companies(session, deleted=False)
        company_id = all_companies[0].id
        vacs_list = []
        for language in Languages:
            for grade in Grades:
                vac = VacancyCreateSchema(
                    title=grade + "_" + language,
                    lang=language,
                    grade=grade,
                    company_id=company_id,
                    link=grade + "_" + language + "_url",
                    experience=randint(0, 10),
                )
                vacs_list.append(vac)
        await create_vacancies(session, vacs_list)
