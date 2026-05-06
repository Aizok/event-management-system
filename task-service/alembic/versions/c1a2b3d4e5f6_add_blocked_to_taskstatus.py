"""add BLOCKED to taskstatus

Revision ID: c1a2b3d4e5f6
Revises: 44663d097cca
Create Date: 2026-05-05 13:45:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c1a2b3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "44663d097cca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE taskstatus ADD VALUE IF NOT EXISTS 'BLOCKED'")


def downgrade() -> None:
    # PostgreSQL does not support dropping a single enum value safely.
    pass
