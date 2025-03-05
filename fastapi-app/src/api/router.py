from fastapi import APIRouter, Depends, status

from src.config import get_settings
from src.api.endpoints import vacancies_router, companies_router

settings = get_settings()

# api_router = APIRouter(prefix=settings.API_PREFIX)
main_router = APIRouter()
main_router.include_router(vacancies_router, prefix="/vacancies", tags=["Вакансии"])
main_router.include_router(companies_router, prefix="/companies", tags=["Компании"])
