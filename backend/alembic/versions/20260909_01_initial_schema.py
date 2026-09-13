"""Create the SQLAlchemy Core academic advisor schema.

Revision ID: 20260909_01
Revises:
Create Date: 2026-09-09
"""

import sqlalchemy as sa

from alembic import op

revision = "20260909_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "students",
        sa.Column("student_id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("major", sa.String(length=120), nullable=False),
        sa.Column("academic_year", sa.String(length=40), nullable=False),
        sa.Column("gpa", sa.Float(), nullable=False),
        sa.Column("attendance_rate", sa.Float(), nullable=False),
        sa.Column("assignment_completion_rate", sa.Float(), nullable=False),
        sa.Column("failed_credits", sa.Integer(), nullable=False),
    )
    op.create_table(
        "courses",
        sa.Column("course_id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("code", sa.String(length=30), nullable=False, unique=True),
        sa.Column("department", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("credits", sa.Integer(), nullable=False),
    )
    op.create_table(
        "skills",
        sa.Column("skill_id", sa.Integer(), primary_key=True),
        sa.Column("skill_name", sa.String(length=120), nullable=False, unique=True),
        sa.Column("category", sa.String(length=120), nullable=False),
    )
    op.create_table(
        "student_skills",
        sa.Column(
            "student_id",
            sa.Integer(),
            sa.ForeignKey("students.student_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "skill_id",
            sa.Integer(),
            sa.ForeignKey("skills.skill_id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_table(
        "student_courses",
        sa.Column(
            "student_id",
            sa.Integer(),
            sa.ForeignKey("students.student_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "course_id",
            sa.Integer(),
            sa.ForeignKey("courses.course_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("grade", sa.String(length=8), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
    )
    op.create_table(
        "course_embeddings",
        sa.Column(
            "course_id",
            sa.Integer(),
            sa.ForeignKey("courses.course_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("embedding", sa.LargeBinary(), nullable=False),
    )
    op.create_table(
        "prediction_history",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "student_id",
            sa.Integer(),
            sa.ForeignKey("students.student_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("risk_level", sa.String(length=30), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_table(
        "recommendation_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "student_id",
            sa.Integer(),
            sa.ForeignKey("students.student_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("recommended_course_ids", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("recommendation_logs")
    op.drop_table("prediction_history")
    op.drop_table("course_embeddings")
    op.drop_table("student_courses")
    op.drop_table("student_skills")
    op.drop_table("skills")
    op.drop_table("courses")
    op.drop_table("students")
