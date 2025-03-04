from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import get_settings


def init_app():
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        # on startup
        print(settings.TITLE)
        print(settings.TEST_V)
        yield
        # on shutdown

    server = FastAPI(
        title=settings.TITLE,
        lifespan=lifespan,
    )

    return server
