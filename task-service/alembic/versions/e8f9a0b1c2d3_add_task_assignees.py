"""add task_assignees table and backfill from tasks.assignee_id

Revision ID: e8f9a0b1c2d3
Revises: c1a2b3d4e5f6
Create Date: 2026-05-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e8f9a0b1c2d3"
down_revision: Union[str, Sequence[str], None] = "c1a2b3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    taskassigneestatus = postgresql.ENUM(
        "pending",
        "accepted",
        "declined",
        name="taskassigneestatus",
        create_type=False,
    )
    taskassigneestatus.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "task_assignees",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", taskassigneestatus, nullable=False),
        sa.Column("invited_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id", "user_id", name="uq_task_assignees_task_user"),
    )
    op.create_index(op.f("ix_task_assignees_id"), "task_assignees", ["id"], unique=False)
    op.create_index(op.f("ix_task_assignees_task_id"), "task_assignees", ["task_id"], unique=False)
    op.create_index(op.f("ix_task_assignees_user_id"), "task_assignees", ["user_id"], unique=False)

    op.execute(
        sa.text(
            """
            INSERT INTO task_assignees (task_id, user_id, status, invited_by, created_at, responded_at)
            SELECT t.id, t.assignee_id, 'accepted', NULL, now(), now()
            FROM tasks t
            WHERE t.assignee_id IS NOT NULL
              AND NOT EXISTS (
                SELECT 1 FROM task_assignees ta
                WHERE ta.task_id = t.id AND ta.user_id = t.assignee_id
              )
            """
        )
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_task_assignees_user_id"), table_name="task_assignees")
    op.drop_index(op.f("ix_task_assignees_task_id"), table_name="task_assignees")
    op.drop_index(op.f("ix_task_assignees_id"), table_name="task_assignees")
    op.drop_table("task_assignees")
    taskassigneestatus = postgresql.ENUM(
        "pending",
        "accepted",
        "declined",
        name="taskassigneestatus",
        create_type=False,
    )
    taskassigneestatus.drop(op.get_bind(), checkfirst=True)
