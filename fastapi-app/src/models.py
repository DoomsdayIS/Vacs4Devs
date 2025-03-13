from contextlib import suppress
from datetime import datetime
from uuid import UUID as PY_UUID
from uuid import uuid4

from sqlalchemy import MetaData, ForeignKey
from sqlalchemy import (
    String,
    func,
)
from sqlalchemy.dialects.postgresql import ENUM, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    registry,
    DeclarativeBase,
    relationship,
)

from src.choices import Companies, Grades, Languages
from src.constants import (
    POSTGRES_INDEXES_NAMING_CONVENTION,
    DESCRIPTION_STR_LENGTH,
    URL_LENGTH,
    NAME_STR_LENGTH,
)

mapper_registry = registry()


class Base(DeclarativeBase):
    __abstract__ = True
    metadata = MetaData(naming_convention=POSTGRES_INDEXES_NAMING_CONVENTION)

    id: Mapped[PY_UUID] = mapped_column(UUID, primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    deleted_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    @classmethod
    @declared_attr.directive
    def __tablename__(cls) -> str:
        symbols = [s if s.islower() else ("_" + s).lower() for s in cls.__name__]
        return "".join(symbols)[1:]

    def to_dict(self, exclude: list[str] | None = None):
        db_obj_dict = self.__dict__.copy()
        del db_obj_dict["_sa_instance_state"]
        for exc in exclude or []:
            with suppress(KeyError):
                del db_obj_dict[exc]
        return db_obj_dict


class Company(Base):
    name: Mapped[Companies] = mapped_column(
        ENUM(Companies, name="company_name"),
        unique=True,
        comment="",
    )
    description: Mapped[str | None] = mapped_column(String(DESCRIPTION_STR_LENGTH))
    company_url: Mapped[str | None] = mapped_column(String(URL_LENGTH))
    company_vacs_url: Mapped[str] = mapped_column(
        String(URL_LENGTH),
        unique=True,
        comment="",
    )


class Vacancy(Base):
    title: Mapped[str] = mapped_column(String(NAME_STR_LENGTH))
    grade: Mapped[Grades] = mapped_column(
        ENUM(Grades, name="vac_grade"),
    )
    lang: Mapped[Languages] = mapped_column(
        ENUM(Languages, name="language"),
    )
    experience: Mapped[int] = mapped_column(comment="Мин количество лет опыта")
    link: Mapped[str] = mapped_column(
        String(URL_LENGTH),
        unique=True,
        comment="Vac link",
    )
    company_id: Mapped[PY_UUID] = mapped_column(
        ForeignKey("company.id", ondelete="CASCADE")
    )
    company: Mapped[Company] = relationship(cascade="all, delete")


class Subscriber(Base):
    name: Mapped[str] = mapped_column(String(NAME_STR_LENGTH))
    email: Mapped[str] = mapped_column(String(NAME_STR_LENGTH), unique=True)
    lang: Mapped[Languages] = mapped_column(
        ENUM(Languages, name="language"),
    )
    grade: Mapped[Grades] = mapped_column(ENUM(Grades, name="vac_grade"), nullable=True)
