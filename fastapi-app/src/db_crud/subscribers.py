from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Subscriber
from src.schemas import SubscriberCreateSchema, SubscriberUpdateSchema


async def get_subscriber_by_email(
    session: AsyncSession, email: str
) -> Sequence[Subscriber]:
    query = select(Subscriber).where(Subscriber.email == email)
    subscriber = await session.scalars(query)
    return subscriber.all()


async def create_subscriber(
    session: AsyncSession, subs_schema: SubscriberCreateSchema
) -> Subscriber:
    subscriber = Subscriber(**subs_schema.model_dump())
    session.add(subscriber)
    await session.commit()
    await session.refresh(subscriber)
    return subscriber


async def delete_subscriber(session: AsyncSession, subscriber: Subscriber):
    await session.delete(subscriber)
    await session.commit()


async def update_subscriber(
    session: AsyncSession,
    subscriber: Subscriber,
    updated_fields: SubscriberUpdateSchema,
):
    updated_fields = updated_fields.model_dump()
    for field in updated_fields:
        if updated_fields[field]:
            setattr(subscriber, field, updated_fields[field])
    session.add(subscriber)
    await session.commit()
    await session.refresh(subscriber)
    return subscriber
