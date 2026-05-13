"""drop phone unique index

Revision ID: 7f9c2d1a4b8e
Revises: 04ce969e34a2
Create Date: 2026-05-12 13:45:00

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "7f9c2d1a4b8e"
down_revision: Union[str, Sequence[str], None] = "04ce969e34a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_user_profiles_phone", table_name="user_profiles")
    op.create_index("ix_user_profiles_phone", "user_profiles", ["phone"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_profiles_phone", table_name="user_profiles")
    op.create_index("ix_user_profiles_phone", "user_profiles", ["phone"], unique=True)
