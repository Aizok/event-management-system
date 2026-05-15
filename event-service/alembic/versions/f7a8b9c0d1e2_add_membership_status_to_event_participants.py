"""add membership_status to event_participants

Revision ID: f7a8b9c0d1e2
Revises: c80aeb6b279c, 9d4f7a2a8b31
Create Date: 2026-05-15 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f7a8b9c0d1e2"
down_revision: Union[str, Sequence[str], None] = ("c80aeb6b279c", "9d4f7a2a8b31")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    membershipstatus = postgresql.ENUM(
        "pending",
        "active",
        "declined",
        name="membershipstatus",
        create_type=False,
    )
    membershipstatus.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "event_participants",
        sa.Column(
            "membership_status",
            membershipstatus,
            nullable=False,
            server_default="active",
        ),
    )
    op.alter_column(
        "event_participants",
        "membership_status",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("event_participants", "membership_status")
    membershipstatus = postgresql.ENUM(
        "pending",
        "active",
        "declined",
        name="membershipstatus",
        create_type=False,
    )
    membershipstatus.drop(op.get_bind(), checkfirst=True)
