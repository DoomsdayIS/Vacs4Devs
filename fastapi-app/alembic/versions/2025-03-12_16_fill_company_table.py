"""empty message

Revision ID: 1dbf0bc14d3b
Revises: f3d5aa0f877f
Create Date: 2025-03-12 16:09:31.014424

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1dbf0bc14d3b"
down_revision: Union[str, None] = "f3d5aa0f877f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sqltext="""
        INSERT INTO company (id, name, description, company_url, company_vacs_url)
        VALUES
        (gen_random_uuid (), 'SELECTEL', 'Selectel («Селектел») — российская технологическая компания, предоставляющая облачные инфраструктурные сервисы и услуги дата-центров.', 'https://selectel.ru/', 'https://selectel.ru/careers/all?code=backend,frontend'),
        (gen_random_uuid (), 'X5', 'X5 Group (ранее — X5 Retail Group) — российская продуктовая розничная торговая компания, управляющая торговыми сетями «Пятёрочка», «Перекрёсток», «Чижик», «Около», «Виктория», «Красный яр» и «Слата».', 'https://www.x5.ru', 'https://x5-tech.ru/vacancy?directionIds=660e855270131eafa8d27678'),
        (gen_random_uuid (), 'AVIASALES', 'Авиасейлс (Aviasales) — российский поисковик авиабилетов, существующий с 2007 года.', 'https://www.aviasales.ru/', 'https://www.aviasales.ru/about/vacancies')
        ON CONFLICT DO NOTHING;
        """
    )


def downgrade() -> None:
    pass
