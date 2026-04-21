"""change field names

Revision ID: a1e69ba7a114
Revises: e2e85b05d150
Create Date: 2026-04-21 12:41:08.756935

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1e69ba7a114'
down_revision: Union[str, Sequence[str], None] = 'e2e85b05d150'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('events', 'start_date', new_column_name='start_time')
    op.alter_column('events', 'end_date', new_column_name='end_time')


def downgrade() -> None:
    op.alter_column('events', 'start_time', new_column_name='start_date')
    op.alter_column('events', 'end_time', new_column_name='end_date')
