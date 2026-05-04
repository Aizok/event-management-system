"""add event time check constraint

Revision ID: 9d4f7a2a8b31
Revises: e2e85b05d150
Create Date: 2026-05-04 15:55:00.000000
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "9d4f7a2a8b31"
down_revision: Union[str, Sequence[str], None] = "e2e85b05d150"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_events_end_time_gte_start_time",
        "events",
        "end_time >= start_time"
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_events_end_time_gte_start_time",
        "events",
        type_="check"
    )
