from typing import Annotated

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.database import get_async_session
from src.db_crud.subscribers import (
    get_subscriber_by_email,
    create_subscriber,
    delete_subscriber,
    update_subscriber,
)
from src.schemas import (
    SubscriberCreateSchema,
    SubscriberRetrieveSchema,
    SubscriberUpdateSchema,
)

router = APIRouter()
CurrentSession = Annotated[AsyncSession, Depends(get_async_session)]


@router.get("/{email}")
async def get_by_email(session: CurrentSession, email: str) -> SubscriberRetrieveSchema:
    subscriber = await get_subscriber_by_email(session, email)
    if not subscriber:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return SubscriberRetrieveSchema(**subscriber[0].to_dict())


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_one_subscriber(
    session: CurrentSession, sub_schema: SubscriberCreateSchema
) -> SubscriberRetrieveSchema:
    check_subscriber = await get_subscriber_by_email(session, sub_schema.email)
    if check_subscriber:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    subscriber = await create_subscriber(session, sub_schema)
    return SubscriberRetrieveSchema(**subscriber.to_dict())


@router.delete("/{email}")
async def delete_by_email(session: CurrentSession, email: str) -> None:
    subscriber = await get_subscriber_by_email(session, email)
    if not subscriber:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    await delete_subscriber(session, subscriber[0])


@router.put("/{email}")
async def update_by_email(
    session: CurrentSession, email: str, sub_schema: SubscriberUpdateSchema
) -> SubscriberRetrieveSchema:
    subscriber = await get_subscriber_by_email(session, email)
    if not subscriber:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    subscriber = await update_subscriber(session, subscriber[0], sub_schema)
    return SubscriberRetrieveSchema(**subscriber.to_dict())
