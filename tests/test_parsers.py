import pytest
from typing_extensions import assert_type

from src.choices import Languages, Grades
from src.parsers import (
    ALL_ACTUAL_PARSERS,
    AviasalesVacancyParser,
    VacancyLink,
    SelectelVacancyParser,
    X5VacancyParser,
)
from src.schemas import VacancyCreateSchema
from src.utils import retry


@pytest.mark.asyncio(loop_scope="session")
async def test_all_vacancy_list():
    parsers = ALL_ACTUAL_PARSERS
    for parser in parsers:
        links = await parser.get_all_actual_vacancy_links()
        assert len(links) > 0
        assert_type(links[0], VacancyLink)


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(
    "vacancy_link_url, parser, lang, grade, return_type",
    [
        (
            "https://www.aviasales.ru/about/vacancies/3919286",
            AviasalesVacancyParser,
            Languages.C_SHARP,
            Grades.MIDDLE,
            VacancyCreateSchema,
        ),
        (
            "https://selectel.ru/careers/all/vacancy/1088/",
            SelectelVacancyParser,
            Languages.GO,
            Grades.MIDDLE,
            VacancyCreateSchema,
        ),
        (
            "https://x5-tech.ru/vacancy/senior-pythondeveloper",
            X5VacancyParser,
            Languages.PYTHON,
            Grades.SENIOR,
            VacancyCreateSchema,
        ),
    ],
)
async def test_vacancy_schema_from_vacancy_link(
    vacancy_link_url, parser, lang, grade, return_type
):
    retry_decor = retry(2, delay=15, backoff=2, exceptions=(Exception,))
    wrapped = retry_decor(parser.vacancy_schema_from_vacancy_link)
    vac_schema = await wrapped(vacancy_link_url)
    assert_type(vac_schema, return_type)
    if vac_schema is not None:
        assert vac_schema.lang == lang
        assert vac_schema.grade == grade
