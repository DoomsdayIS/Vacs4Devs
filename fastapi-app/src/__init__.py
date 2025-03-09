from contextlib import asynccontextmanager
from src.database import sessionmanager

from fastapi import FastAPI

from src.config import get_settings


def init_app(init_db=True):
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        # on startup
        if init_db:
            sessionmanager.init(settings.SQLALCHEMY_DATABASE_URL.unicode_string())

        yield
        # on shutdown
        if init_db:
            if sessionmanager._engine is not None:
                await sessionmanager.close()

    server = FastAPI(
        title=settings.TITLE,
        openapi_url=settings.OPENAPI_URL,
        docs_url=settings.DOCS_URL,
        redoc_url=None,
        description="description",
        summary="summary",
        version="0.0.1",
        contact={
            "name": "Ivan Sheremet",
            "email": "ivan.sheremet.sus@bk.ru",
        },
        lifespan=lifespan,
    )

    from src.api import main_router

    server.include_router(main_router)

    return server
