from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from uuid import UUID

import httpx
from bs4 import BeautifulSoup
from chromedriver_py import binary_path  # this will get you the path variable
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from selenium import webdriver
from selenium.webdriver.common.by import By

from src.choices import Grades, Languages
from src.config import get_settings
from src.schemas import VacancyCreateSchema

settings = get_settings()
gpt_client = AsyncOpenAI(api_key=settings.GPT_API_KEY)
SELENIUM_SERVICE = webdriver.ChromeService(executable_path=binary_path)


VACANCY_ANALYZE_PROMPT = """
В следующих запросах (сообщение начинающееся со слова ЗАПРОС) я ожидаю что по отправленному тебе коду со страницы вакансии
ты отпределишь:
1) необходимый опыт от кандидата: количество лет, целое число.
Если в тексте нет явного указания на требуемый опыт в годах, то надо проставить опыт в зависимости от ожидаемого уровня кандидата по следующему правилу:
intern: 0, junior:1, middle: 2, senior: 3, team_lead: 3
2) один основной требуемый язык программирования в вакансии из списка: (go, python, java, ios, c_sharp, frontend, ios, other).
frontend это javasript, ios как правило это swift. other это когда основного языка, который требуется в вакансии, в вакансии нет в списке. 
3) ожидаемый уровень кандидата: junior, middle, senior, team_lead, intern. Если в вакансии прямо не указан требуемый уровень кандидата, считать по умолчанию middle
Ты должен вернуть json объект, который будет представлять информацию в следующем виде:

{
    experience: int or None // Целое число лет ожидаемого опыта от кандидата,
    grade: string // (junior, middle, senior, team_lead, intern),
    lang: string // (go, python, java, ios, c_sharp, frontend, ios, other)
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


class CompanyVacanciesParser(ABC):

    @property
    @abstractmethod
    def company_id(self):
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
    company_id = UUID("c2fbc96f-2484-4c37-95d4-9fc60d5b6b8e")

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
    company_id = UUID("67d25972-a93b-4da0-bfaa-5d8d3a8de78b")

    @classmethod
    async def get_all_actual_vacancy_links(cls) -> list[VacancyLink]:
        driver = webdriver.Chrome(service=SELENIUM_SERVICE)
        driver.get("https://selectel.ru/careers/all?code=backend,frontend")
        elements = driver.find_elements(By.CLASS_NAME, "card__link")
        vacancies_links = []
        for element in elements:
            vacancies_links.append(
                VacancyLink(link_text=element.get_attribute("href"), parser_class=cls)
            )
        driver.close()
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
            vacancy_desc = soup.find("div", class_="short-info__description").find_all(
                "p"
            )
            vd = []
            for d in vacancy_desc:
                vd.append(d.text)
            vacancy_desc = " ".join(vd)
            vacancy_reqs = soup.find("div", class_="vacancy__about").find_all("ul")[1]
        except AttributeError:
            return None

        if not vacancy_reqs or not vacancy_title or not vacancy_desc:
            return None
        vacancy_info = f"Название вакансии {vacancy_title}. Описание: {vacancy_desc}. Требования: {vacancy_reqs}"
        return await cls._create_vacancy_schema(
            vacancy_title=vacancy_title,
            vacancy_info=vacancy_info,
            vacancy_link_text=vacancy_link_text,
        )


class X5VacancyParser(CompanyVacanciesParser):
    company_id = UUID("96b7a729-b1a0-4e94-80f8-57a9350daafd")

    @classmethod
    async def get_all_actual_vacancy_links(cls) -> list[VacancyLink]:
        driver = webdriver.Chrome(service=SELENIUM_SERVICE)
        driver.get("https://x5-tech.ru/vacancy?directionIds=660e855270131eafa8d27678")
        spt = 0.3
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
            qst_index = text.rindex("?")
            vacancies_links.append(
                VacancyLink(link_text=text[:qst_index], parser_class=cls)
            )
        driver.close()
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
