import pytest
from httpx import AsyncClient, ASGITransport

from src import init_app
from src.choices import Companies, Languages, Grades
from src.schemas import CompanyRetrieveSchema, VacancyRetrieveSchema


@pytest.mark.asyncio(loop_scope="session")
async def test_get_companies(fill_companies_table):
    async with AsyncClient(
        transport=ASGITransport(app=init_app(init_db=False)), base_url="http://test"
    ) as ac:
        rs = await ac.get("/companies/all")
    companies = rs.json()
    assert len(companies) == len(Companies)
    CompanyRetrieveSchema(**companies[0])


@pytest.mark.asyncio(loop_scope="session")
async def test_get_vacancies(fill_vacancies_table):
    async with AsyncClient(
        transport=ASGITransport(app=init_app(init_db=False)), base_url="http://test"
    ) as ac:
        params_1 = {}
        rs_1 = await ac.get("/vacancies/all", params=params_1)
        params_2 = {"lang": Languages.GO, "grade": Grades.MIDDLE}
        rs_2 = await ac.get("/vacancies/all", params=params_2)
    vacancies_1 = rs_1.json()
    vacancies_2 = rs_2.json()
    assert len(vacancies_1) == len(Languages) * len(Grades)
    assert len(vacancies_2) == 1
    VacancyRetrieveSchema(**vacancies_1[0])
