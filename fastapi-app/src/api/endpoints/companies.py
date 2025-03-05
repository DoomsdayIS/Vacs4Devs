from typing import Annotated

from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.db_crud import companies as crud_companies
from src.schemas import CompanyRetrieveSchema, CompanyCreateSchema

router = APIRouter()
CurrentSession = Annotated[AsyncSession, Depends(get_async_session)]


@router.get("/test1", response_model=list[CompanyRetrieveSchema])
async def get_companies(session: CurrentSession):
    companies = await crud_companies.get_all_companies(session=session)
    return companies


@router.post("/test2", response_model=CompanyRetrieveSchema)
async def create_company(session: CurrentSession, company: CompanyCreateSchema):
    company = await crud_companies.create_company(
        session=session, company_create=company
    )
    return company
