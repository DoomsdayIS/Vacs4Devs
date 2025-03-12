from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod

import httpx
from bs4 import BeautifulSoup
from openai import AsyncOpenAI, PermissionDeniedError
from pydantic import BaseModel, Field
from selenium import webdriver
from selenium.webdriver.common.by import By
from sqlalchemy.ext.asyncio import AsyncSession

from src.choices import Grades, Languages, Companies
from src.config import get_settings
from src.db_crud.companies import get_all_companies
from src.schemas import VacancyCreateSchema

settings = get_settings()
gpt_client = AsyncOpenAI(api_key=settings.GPT_API_KEY, timeout=5)


VACANCY_ANALYZE_PROMPT = """
В следующих запросах (сообщение начинающееся со слова ЗАПРОС) я ожидаю что по отправленному тебе коду со страницы вакансии
ты отпределишь:
1) необходимый опыт от кандидата: количество лет, целое число.
Если в тексте нет явного указания на требуемый опыт в годах, то надо проставить опыт в зависимости от ожидаемого уровня кандидата по следующему правилу:
intern: 0, junior:1, middle: 2, senior: 3, team_lead: 3
2) один основной требуемый язык программирования в вакансии из списка: (go, python, java, ios, c_sharp, frontend, ios, other).
frontend это javasript, ios как правило это swift. other это когда основного языка, который требуется в вакансии, в вакансии нет в списке. 
3) ожидаемый уровень кандидата: junior, middle, senior, team_lead, intern. Если в вакансии прямо не указан требуемый уровень кандидата, считать по умолчанию middle
4) является ли вакансия вакансией разработчика/developer-а/тимлида/: вернуть 1 если является, 0 если это вакансия менеджера, аналитика, маркетолога и т.п.
В близких ситуациях лучше возвращать 1. Если выявлен язык программирования ( не other ) то всегда возвращать 1.
Ты должен вернуть json объект, который будет представлять информацию в следующем виде:

{
    experience: int or None // Целое число лет ожидаемого опыта от кандидата,
    grade: string // (junior, middle, senior, team_lead, intern),
    lang: string // (go, python, java, ios, c_sharp, frontend, ios, other)
    is_dev" int // 0 или 1 
}

"""


async def gpt_analyze_vacancy_info(info):
    response = await gpt_client.chat.completions.create(
        model="gpt-4o-mini",
        store=True,
        response_format={"type": "json_object"},
        messages=[
            {"role": "developer", "content": VACANCY_ANALYZE_PROMPT},
            {
                "role": "user",
                "content": f"ЗАПРОС:{info}",
            },
        ],
    )
    return response.choices[0].message.content


class GptResponse(BaseModel):
    grade: Grades
    experience: int = Field(ge=0)
    lang: Languages
    is_dev: int = Field(ge=0, le=1)


class CompanyVacanciesParser(ABC):

    company_id = None

    @property
    @abstractmethod
    def company_name(self):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    async def get_all_actual_vacancy_links(cls) -> list[VacancyLink]:
        pass

    @classmethod
    @abstractmethod
    async def vacancy_schema_from_vacancy_link(
        cls, vacancy_link_text: str
    ) -> VacancyCreateSchema | None:
        pass

    @classmethod
    async def _create_vacancy_schema(
        cls, vacancy_title: str, vacancy_info: str, vacancy_link_text: str
    ):
        gpt_response = await gpt_analyze_vacancy_info(vacancy_info)
        gpt_response = GptResponse(**json.loads(gpt_response))
        if gpt_response.is_dev == 0:
            return None
        return VacancyCreateSchema(
            title=vacancy_title,
            grade=gpt_response.grade,
            lang=gpt_response.lang,
            experience=gpt_response.experience,
            link=vacancy_link_text,
            company_id=cls.company_id,
        )


class VacancyLink:
    def __init__(self, link_text: str, parser_class) -> None:
        self.link_text = link_text
        self.parser_class = parser_class


class AviasalesVacancyParser(CompanyVacanciesParser):
    company_name = Companies.AVIASALES

    @classmethod
    async def get_all_actual_vacancy_links(cls) -> list[VacancyLink]:
        vacancies_page = httpx.get("https://www.aviasales.ru/about/vacancies")
        soup = BeautifulSoup(vacancies_page.text, "html.parser")
        vacancies_links = []
        for link in soup.find_all("a"):
            if link.get("href").startswith("/about/vacancies/"):
                vacancies_links.append(
                    VacancyLink(
                        link_text="https://www.aviasales.ru" + link.get("href"),
                        parser_class=cls,
                    )
                )
        return vacancies_links

    @classmethod
    async def vacancy_schema_from_vacancy_link(
        cls, vacancy_link_text: str
    ) -> VacancyCreateSchema | None:
        async with httpx.AsyncClient() as http_client:
            vacancy_page = await http_client.get(vacancy_link_text)
        soup = BeautifulSoup(vacancy_page.text, "html.parser")
        try:
            vacancy_title = soup.find("title").text
            vacancy_title = (
                vacancy_title.lstrip("Работа в Авиасейлс — ")
                if vacancy_title.startswith("Работа в Авиасейлс — ")
                else vacancy_title
            )
            vacancy_reqs = soup.find_all("div", class_="vacancy__requirements")
        except AttributeError:
            return None
        if not vacancy_reqs or not vacancy_title:
            return None
        vacancy_info = f"Название вакансии {vacancy_title}. Требования: {vacancy_reqs}"
        return await cls._create_vacancy_schema(
            vacancy_title=vacancy_title,
            vacancy_info=vacancy_info,
            vacancy_link_text=vacancy_link_text,
        )


class SelectelVacancyParser(CompanyVacanciesParser):
    company_name = Companies.SELECTEL

    @classmethod
    async def get_all_actual_vacancy_links(cls) -> list[VacancyLink]:
        options = webdriver.ChromeOptions()
        options.add_argument("--ignore-ssl-errors=yes")
        options.add_argument("--ignore-certificate-errors")
        driver = webdriver.Remote(
            command_executor=f"http://{settings.SELENIUM_HOST}:4444/wd/hub",
            options=options,
        )
        driver.get("https://selectel.ru/careers/all?code=backend,frontend")
        elements = driver.find_elements(By.CLASS_NAME, "card__link")
        vacancies_links = []
        for element in elements:
            link_text = element.get_attribute("href")
            r_index = link_text.rindex("/", 0, -1)
            link_text = (
                "https://api.selectel.ru/proxy/public/employee/api/public/vacancies/"
                + link_text[r_index + 1 : -1]
            )
            vacancies_links.append(VacancyLink(link_text=link_text, parser_class=cls))
        driver.close()
        driver.quit()
        return vacancies_links

    @classmethod
    async def vacancy_schema_from_vacancy_link(
        cls, vacancy_link_text: str
    ) -> VacancyCreateSchema | None:
        async with httpx.AsyncClient() as http_client:
            vacancy_page = await http_client.get(vacancy_link_text)
        try:
            vac_dict_info = json.loads(vacancy_page.text)
            vacancy_title = vac_dict_info["title"]
            vacancy_desc = vac_dict_info["detailed_desc"]
        except (TypeError, KeyError, AttributeError):
            return None
        if not vacancy_title or not vacancy_desc:
            return None
        vacancy_info = f"Название вакансии {vacancy_title}. Описание: {vacancy_desc}"
        return await cls._create_vacancy_schema(
            vacancy_title=vacancy_title,
            vacancy_info=vacancy_info,
            vacancy_link_text=vacancy_link_text,
        )


class X5VacancyParser(CompanyVacanciesParser):
    company_name = Companies.X5

    @classmethod
    async def get_all_actual_vacancy_links(cls) -> list[VacancyLink]:
        options = webdriver.ChromeOptions()
        options.add_argument("--ignore-ssl-errors=yes")
        options.add_argument("--ignore-certificate-errors")
        driver = webdriver.Remote(
            command_executor=f"http://{settings.SELENIUM_HOST}:4444/wd/hub",
            options=options,
        )
        driver.get("https://x5-tech.ru/vacancy?directionIds=660e855270131eafa8d27678")
        spt = 1
        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(spt)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        elements = driver.find_elements(By.CLASS_NAME, "VacanciesItem_title__iBYZP")
        vacancies_links = []
        for element in elements:
            text = element.get_attribute("href")
            qst_index = text.rindex("?") if "?" in text else None
            if qst_index is not None:
                text = text[:qst_index]
            vacancies_links.append(VacancyLink(link_text=text, parser_class=cls))
        driver.close()
        driver.quit()
        return vacancies_links

    @classmethod
    async def vacancy_schema_from_vacancy_link(
        cls, vacancy_link_text: str
    ) -> VacancyCreateSchema | None:
        async with httpx.AsyncClient() as http_client:
            vacancy_page = await http_client.get(vacancy_link_text)
        soup = BeautifulSoup(vacancy_page.text, "html.parser")
        try:
            vacancy_title = soup.find("title").text
            vacancy_title = (
                vacancy_title.rstrip(" — открытая вакансия в команде X5 Tech")
                if vacancy_title.endswith(" — открытая вакансия в команде X5 Tech")
                else vacancy_title
            )
            vacancy_reqs = soup.find_all(
                "div", class_="VacancyPage_descriptionText___AFQG"
            )[-1]
        except AttributeError:
            return None
        if not vacancy_title or not vacancy_reqs:
            return None
        vacancy_info = f"Название вакансии {vacancy_title}. Требования: {vacancy_reqs}"
        return await cls._create_vacancy_schema(
            vacancy_title=vacancy_title,
            vacancy_info=vacancy_info,
            vacancy_link_text=vacancy_link_text,
        )


ALL_ACTUAL_PARSERS = [AviasalesVacancyParser, SelectelVacancyParser, X5VacancyParser]


async def add_company_id_to_parsers(session: AsyncSession):
    companies = await get_all_companies(session, deleted=False)
    companies_dict = {}
    for company in companies:
        companies_dict[company.name] = company.id
    for parser in ALL_ACTUAL_PARSERS:
        parser.company_id = (
            companies_dict[parser.company_name]
            if parser.company_name in companies_dict
            else None
        )


async def test_openai():
    try:
        await gpt_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Write hello world"}],
        )
    except PermissionDeniedError:
        return False
    return True
