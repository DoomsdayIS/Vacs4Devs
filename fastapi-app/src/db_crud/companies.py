from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence

from src.models import Company
from sqlalchemy import select

from src.schemas import CompanyCreateSchema


async def get_all_companies(
    session: AsyncSession,
    deleted: bool,
) -> Sequence[Company]:
    stmt = select(Company).order_by(Company.created_at)
    if not deleted:
        stmt = stmt.filter(Company.deleted_at.is_(None))
    result = await session.scalars(stmt)
    return result.all()


async def create_company(
    session: AsyncSession, company_create: CompanyCreateSchema
) -> Company:
    company = Company(**company_create.model_dump())
    session.add(company)
    await session.commit()
    await session.refresh(company)
    return company


async def create_companies(
    session: AsyncSession, companies: list[CompanyCreateSchema]
) -> list[Company]:
    objs = []
    for company in companies:
        db_obj = Company(**company.model_dump())
        objs.append(db_obj)
    session.add_all(objs)
    await session.commit()
    for db_obj in objs:
        await session.refresh(db_obj)
    return objs
