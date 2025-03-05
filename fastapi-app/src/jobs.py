import asyncio
from datetime import datetime, timezone
from typing import Annotated

from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.db_crud import vacancies as crud_vacancies
from src.parsers import ALL_ACTUAL_PARSERS
from src.schemas import VacancyRetrieveSchema
from src.utils import retry

CurrentSession = Annotated[AsyncSession, Depends(get_async_session)]


async def daily_vacancy_processing(session: AsyncSession):
    vacancies_models = await crud_vacancies.get_vacancies(
        session=session,
        lang=None,
        grade=None,
        min_experience=0,
        max_experience=100,
        deleted=False,
    )
    vacancies_dict = {}
    for vacancy in vacancies_models:
        vacancies_dict[vacancy.link] = [vacancy, True]

    all_vacancies = []
    for parser in ALL_ACTUAL_PARSERS:
        parser_vacancies = await parser.get_all_actual_vacancy_links()
        all_vacancies.extend(parser_vacancies)

    new_vacancies = []
    for vac_link in all_vacancies:
        if vac_link.link_text not in vacancies_dict:
            new_vacancies.append(vac_link)
        else:
            vacancies_dict[vac_link.link_text][1] = False
    print(len(new_vacancies))

    objs_to_update = {}
    for link, vac in vacancies_dict.items():
        if vac[1] is True:
            vac_schema = VacancyRetrieveSchema(**vac[0].to_dict())
            vac_schema.deleted_at = datetime.now(tz=timezone.utc)
            objs_to_update[vac[0]] = vac_schema
    await crud_vacancies.update_vacancies(session, objs_to_update)

    new_vacancies_schemas = []
    retry_decor = retry(2, delay=30, backoff=2, exceptions=(Exception,))
    for new_vacancy in new_vacancies:
        wrapped = retry_decor(new_vacancy.parser_class.vacancy_schema_from_vacancy_link)
        res = await wrapped(new_vacancy.link_text)
        await asyncio.sleep(3)
        if res is not None:
            new_vacancies_schemas.append(res)
    await crud_vacancies.create_vacancies(session, new_vacancies_schemas)
