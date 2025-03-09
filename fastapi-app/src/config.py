from functools import lru_cache
from pathlib import Path

from pydantic import (
    PostgresDsn,
    field_validator,
)
from pydantic_core.core_schema import FieldValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env", case_sensitive=True, extra="allow"
    )

    TITLE: str = "vacs4devs"
    API_PREFIX: str = "/api/core"
    OPENAPI_URL: str = API_PREFIX + "/public/openapi.json"
    DOCS_URL: str = API_PREFIX + "/public/docs"

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URL: PostgresDsn | None = None

    GPT_API_KEY: str

    @field_validator("SQLALCHEMY_DATABASE_URL", mode="before")
    def assemble_db_connection_string(
        cls, v: PostgresDsn | None, info: FieldValidationInfo
    ) -> str | PostgresDsn:
        if isinstance(v, str):
            return v
        scheme = "postgresql+asyncpg"
        user = info.data["POSTGRES_USER"]
        password = info.data["POSTGRES_PASSWORD"]
        host = info.data["POSTGRES_HOST"]
        port = info.data["POSTGRES_PORT"]
        path = f'/{info.data["POSTGRES_DB"]}'

        url = f"{scheme}://{user}:{password}@{host}:{port}{path}"
        return PostgresDsn(url)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
