from contextlib import nullcontext as does_not_raise
from random import randint
from types import NoneType
from typing import assert_type

import pytest
from pydantic import ValidationError

from src import sessionmanager
from src.choices import Companies, Languages, Grades
from src.db_crud.companies import create_companies, create_company, get_all_companies
from src.db_crud.vacancies import create_vacancies, create_vacancy
from src.models import Company, Vacancy
from src.schemas import CompanyCreateSchema, VacancyCreateSchema


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(
    "company_name, expectation",
    [
        (Companies.AVIASALES, does_not_raise()),
        ("abobus", pytest.raises(ValidationError)),
    ],
)
async def test_create_company(create_tables, company_name, expectation):
    async with sessionmanager.session() as session:
        with expectation:
            ccs = CompanyCreateSchema(
                name=company_name, company_vacs_url=company_name + "_url"
            )
            company = await create_company(session, ccs)
    if company_name == Companies.AVIASALES:
        assert_type(company, Company)
        assert company.name == Companies.AVIASALES
        assert company.company_vacs_url == Companies.AVIASALES + "_url"
        assert_type(company.company_url, NoneType)
        assert_type(company.description, NoneType)
        assert_type(company.deleted_at, NoneType)


@pytest.mark.asyncio(loop_scope="session")
async def test_create_companies(create_tables):
    async with sessionmanager.session() as session:
        ccs_list = []
        for company_name in Companies:
            ccs = CompanyCreateSchema(
                name=company_name, company_vacs_url=company_name + "_url"
            )
            ccs_list.append(ccs)
        companies = await create_companies(session, ccs_list)
    assert len(companies) == len(Companies)
    assert_type(companies[0], Company)


@pytest.mark.asyncio(loop_scope="session")
async def test_create_vacancy(fill_companies_table):
    async with sessionmanager.session() as session:
        all_companies = await get_all_companies(session, deleted=False)
        company_id = all_companies[0].id
        grade = Grades.MIDDLE
        language = Languages.GO
        vac = VacancyCreateSchema(
            title=grade + "_" + language,
            lang=language,
            grade=grade,
            company_id=company_id,
            link=grade + "_" + language + "_url",
            experience=randint(0, 10),
        )
        vacancy = await create_vacancy(session, vac)
    assert_type(vacancy, Vacancy)
    assert vacancy.title == grade + "_" + language
    assert vacancy.link == grade + "_" + language + "_url"
    assert vacancy.lang == language
    assert vacancy.grade == grade
    assert_type(vacancy.deleted_at, NoneType)


@pytest.mark.asyncio(loop_scope="session")
async def test_create_vacancies(fill_companies_table):
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
        vacancies = await create_vacancies(session, vacs_list)
    assert len(vacancies) == len(Languages) * len(Grades)
    assert_type(vacancies[0], Vacancy)
