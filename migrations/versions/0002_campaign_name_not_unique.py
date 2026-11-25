"""campaigns.name: снять уникальность, добавить обычный индекс

После удаления кампании в Keitaro её название можно занять снова,
а запись о старой кампании в реестре остаётся.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-25
"""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

SQLITE_UQ = "uq_campaigns_name"
POSTGRES_UQ = "campaigns_name_key"
NAMING = {"uq": "uq_%(table_name)s_%(column_0_name)s"}


def _is_sqlite() -> bool:
    return op.get_bind().dialect.name == "sqlite"


def upgrade() -> None:
    if _is_sqlite():
        with op.batch_alter_table("campaigns", naming_convention=NAMING) as batch:
            batch.drop_constraint(SQLITE_UQ, type_="unique")
    else:
        op.drop_constraint(POSTGRES_UQ, "campaigns", type_="unique")
    op.create_index("ix_campaigns_name", "campaigns", ["name"])


def downgrade() -> None:
    op.drop_index("ix_campaigns_name", table_name="campaigns")
    if _is_sqlite():
        with op.batch_alter_table("campaigns") as batch:
            batch.create_unique_constraint(SQLITE_UQ, ["name"])
    else:
        op.create_unique_constraint(POSTGRES_UQ, "campaigns", ["name"])
