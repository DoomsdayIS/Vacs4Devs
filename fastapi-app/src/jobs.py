import asyncio
from datetime import datetime, timezone

from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.config import get_settings
from src.database import sessionmanager
from src.db_crud.vacancies import get_vacancies, update_vacancies, create_vacancies
from src.parsers import ALL_ACTUAL_PARSERS, add_company_id_to_parsers, test_openai
from src.schemas import VacancyRetrieveSchema
from src.utils import retry


async def daily_vacancy_processing() -> None:
    print("JOB STARTED")
    openai_permission = await test_openai()
    if not openai_permission:
        print("NO PERMISSION")
        return
    print("PERMISSION")
    all_vacs_retry_decor = retry(5, delay=5, backoff=2, exceptions=(Exception,))
    vac_retry_decor = retry(2, delay=30, backoff=2, exceptions=(Exception,))

    async with sessionmanager.session() as session:
        await add_company_id_to_parsers(session)
        vacancies_models = await get_vacancies(
            session=session,
            lang=None,
            grade=None,
            min_experience=0,
            max_experience=100,
            deleted=False,
        )
        vacancies_dict = {}
        for vacancy in vacancies_models:
            vacancies_dict[vacancy.Vacancy.link] = [vacancy.Vacancy, True]

        all_vacancies = []
        for parser in ALL_ACTUAL_PARSERS:
            all_vacancies_wrapped = all_vacs_retry_decor(
                parser.get_all_actual_vacancy_links
            )
            parser_vacancies = await all_vacancies_wrapped()
            if parser_vacancies:
                all_vacancies.extend(parser_vacancies)

        new_vacancies = []
        for vac_link in all_vacancies:
            if vac_link.link_text not in vacancies_dict:
                new_vacancies.append(vac_link)
            else:
                vacancies_dict[vac_link.link_text][1] = False

        objs_to_update = {}
        for link, vac in vacancies_dict.items():
            if vac[1] is True:
                vac_schema = VacancyRetrieveSchema(**vac[0].to_dict())
                vac_schema.deleted_at = datetime.now(tz=timezone.utc)
                objs_to_update[vac[0]] = vac_schema

        print("to update ", len(objs_to_update))
        await update_vacancies(session, objs_to_update)

        print("all ", len(all_vacancies))
        print("new ", len(new_vacancies))
        new_vacancies_schemas = []
        for new_vacancy in new_vacancies:
            schema_from_link_wrapped = vac_retry_decor(
                new_vacancy.parser_class.vacancy_schema_from_vacancy_link
            )
            res = await schema_from_link_wrapped(new_vacancy.link_text)
            await asyncio.sleep(3)
            if res is not None:
                new_vacancies_schemas.append(res)
        print("new schemas ", len(new_vacancies_schemas))
        await create_vacancies(session, new_vacancies_schemas)


jobstores = {
    "default": RedisJobStore(
        db=1,
        jobs_key="role_models_jobs",
        run_times_key="role_models_running",
        host=get_settings().REDIS_HOST,
        port=get_settings().REDIS_PORT,
    )
}

scheduler = AsyncIOScheduler(timezone="Europe/Moscow", jobstores=jobstores)

scheduler.add_job(
    daily_vacancy_processing,
    "cron",
    hour=3,
    replace_existing=True,
    id="send_course_start_notifications",
)
