import contextlib
from asyncio import current_task
from contextlib import asynccontextmanager
from typing import Annotated, AsyncIterator

from fastapi import Depends
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)


class DatabaseSessionManager:
    def __init__(self):
        self._engine: AsyncEngine | None = None
        self._sessionmaker: async_sessionmaker | None = None

    def init(
        self,
        host: str,
        echo: bool = False,
        echo_pool: bool = False,
        max_overflow: int = 10,
        pool_size: int = 5,
    ) -> None:
        self._engine = create_async_engine(
            host,
            echo=echo,
            echo_pool=echo_pool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            connect_args={"server_settings": {"jit": "off"}},
        )
        self._sessionmaker = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine,
        )

    async def close(self):
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        await self._engine.dispose()
        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise Exception("DatabaseSessionManager is not initialized")

        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def create_all(self, connection: AsyncConnection, metadata: MetaData):
        await connection.run_sync(metadata.create_all)

    async def drop_all(self, connection: AsyncConnection, metadata: MetaData):
        await connection.run_sync(metadata.drop_all)


sessionmanager = DatabaseSessionManager()


async def get_async_session():
    async with sessionmanager.session() as session:
        yield session


@asynccontextmanager
async def scoped_session():
    scoped_factory = async_scoped_session(
        get_async_session,
        scopefunc=current_task,
    )
    try:
        async with scoped_factory() as s:
            yield s
    finally:
        await scoped_factory.remove()


ScopedSession = Annotated[AsyncSession, Depends(scoped_session)]
