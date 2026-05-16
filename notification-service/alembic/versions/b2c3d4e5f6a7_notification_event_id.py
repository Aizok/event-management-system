"""notification event_id nullable task_id

Revision ID: b2c3d4e5f6a7
Revises: a11c596f9ebe
Create Date: 2026-05-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a11c596f9ebe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("notifications", "task_id", existing_type=sa.Integer(), nullable=True)
    op.add_column("notifications", sa.Column("event_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_notifications_event_id"), "notifications", ["event_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_notifications_event_id"), table_name="notifications")
    op.drop_column("notifications", "event_id")
    op.alter_column("notifications", "task_id", existing_type=sa.Integer(), nullable=False)
