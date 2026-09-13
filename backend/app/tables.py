"""SQLAlchemy Core table definitions. SQLAlchemy ORM is deliberately not used."""

from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    MetaData,
    String,
    Table,
    Text,
    func,
)

metadata = MetaData()
students = Table(
    "students",
    metadata,
    Column("student_id", Integer, primary_key=True),
    Column("name", String(150), nullable=False),
    Column("major", String(120), nullable=False),
    Column("academic_year", String(40), nullable=False),
    Column("gpa", Float, nullable=False),
    Column("attendance_rate", Float, nullable=False),
    Column("assignment_completion_rate", Float, nullable=False),
    Column("failed_credits", Integer, nullable=False),
    Column("interests", Text, nullable=False, server_default=""),
)
courses = Table(
    "courses",
    metadata,
    Column("course_id", Integer, primary_key=True),
    Column("title", String(160), nullable=False),
    Column("code", String(30), nullable=False, unique=True),
    Column("department", String(120), nullable=False),
    Column("description", Text, nullable=False),
    Column("credits", Integer, nullable=False),
)
skills = Table(
    "skills",
    metadata,
    Column("skill_id", Integer, primary_key=True),
    Column("skill_name", String(120), nullable=False, unique=True),
    Column("category", String(120), nullable=False),
)
student_skills = Table(
    "student_skills",
    metadata,
    Column(
        "student_id",
        ForeignKey("students.student_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "skill_id", ForeignKey("skills.skill_id", ondelete="CASCADE"), primary_key=True
    ),
)
student_courses = Table(
    "student_courses",
    metadata,
    Column(
        "student_id",
        ForeignKey("students.student_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "course_id",
        ForeignKey("courses.course_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("grade", String(8), nullable=True),
    Column("status", String(30), nullable=False),
)
course_embeddings = Table(
    "course_embeddings",
    metadata,
    Column(
        "course_id",
        ForeignKey("courses.course_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("embedding", LargeBinary, nullable=False),
)
prediction_history = Table(
    "prediction_history",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column(
        "student_id",
        ForeignKey("students.student_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("risk_level", String(30), nullable=False),
    Column("risk_score", Float, nullable=False),
    Column("academic_indicators", JSON, nullable=True),
    Column("feature_snapshot", JSON, nullable=True),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
)
recommendation_logs = Table(
    "recommendation_logs",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column(
        "student_id",
        ForeignKey("students.student_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("recommended_course_ids", JSON, nullable=False),
    Column("recommendations", JSON, nullable=True),
    Column("academic_guidance", Text, nullable=True),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
)
