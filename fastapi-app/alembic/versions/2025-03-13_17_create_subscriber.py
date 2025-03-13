"""create subscriber

Revision ID: 989966f609df
Revises: 1dbf0bc14d3b
Create Date: 2025-03-13 17:10:54.621678

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "989966f609df"
down_revision: Union[str, None] = "1dbf0bc14d3b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "subscriber",
        sa.Column("name", sa.String(length=127), nullable=False),
        sa.Column("email", sa.String(length=127), nullable=False),
        sa.Column(
            "lang",
            postgresql.ENUM(
                create_type=False,
                name="language",
            ),
            nullable=False,
        ),
        sa.Column(
            "grade",
            postgresql.ENUM(
                create_type=False,
                name="vac_grade",
            ),
            nullable=True,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("subscriber_pkey")),
        sa.UniqueConstraint("email", name=op.f("subscriber_email_key")),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    op.drop_table("subscriber")
    # ### end Alembic commands ###
