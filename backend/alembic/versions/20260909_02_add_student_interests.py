"""Add student interests to drive skills-and-interests recommendations.

Revision ID: 20260909_02
Revises: 20260909_01
Create Date: 2026-09-09
"""

import sqlalchemy as sa

from alembic import op

revision = "20260909_02"
down_revision = "20260909_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "students",
        sa.Column("interests", sa.Text(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("students", "interests")
