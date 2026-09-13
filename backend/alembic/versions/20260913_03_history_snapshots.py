"""Preserve prediction indicators and recommendation details for history.

Revision ID: 20260913_03
Revises: 20260909_02
"""

import sqlalchemy as sa

from alembic import op

revision = "20260913_03"
down_revision = "20260909_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable columns preserve existing events without inventing historical details.
    op.add_column(
        "prediction_history", sa.Column("academic_indicators", sa.JSON(), nullable=True)
    )
    op.add_column(
        "prediction_history", sa.Column("feature_snapshot", sa.JSON(), nullable=True)
    )
    op.add_column(
        "recommendation_logs", sa.Column("recommendations", sa.JSON(), nullable=True)
    )
    op.add_column(
        "recommendation_logs", sa.Column("academic_guidance", sa.Text(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("recommendation_logs", "academic_guidance")
    op.drop_column("recommendation_logs", "recommendations")
    op.drop_column("prediction_history", "feature_snapshot")
    op.drop_column("prediction_history", "academic_indicators")
