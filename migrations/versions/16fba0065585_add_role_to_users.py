"""Add role to users

Revision ID: 16fba0065585
Revises: dea87b69c5c6
Create Date: 2025-06-23 20:59:47.572974

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "16fba0065585"
down_revision: Union[str, None] = "dea87b69c5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "users", sa.Column("role", sa.String(), nullable=False, server_default="user")
    )
    op.alter_column("users", "role", server_default=None)


def downgrade():
    op.drop_column("users", "role")
