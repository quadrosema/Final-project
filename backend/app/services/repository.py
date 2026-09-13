"""Database queries written entirely with SQLAlchemy Core statements."""

from collections.abc import Sequence

from sqlalchemy import delete, insert, select, update

from app.database import engine
from app.ml.risk_model import academic_indicators
from app.tables import (
    course_embeddings,
    courses,
    prediction_history,
    recommendation_logs,
    skills,
    student_skills,
    students,
)


def _skill_names(connection, student_id: int) -> list[str]:
    statement = (
        select(skills.c.skill_name)
        .select_from(student_skills.join(skills))
        .where(student_skills.c.student_id == student_id)
        .order_by(skills.c.skill_name)
    )
    return list(connection.execute(statement).scalars())


def student_with_skills(student_id: int) -> dict | None:
    with engine.connect() as connection:
        student = (
            connection.execute(
                select(students).where(students.c.student_id == student_id)
            )
            .mappings()
            .first()
        )
        if student is None:
            return None
        result = dict(student)
        result["skills"] = _skill_names(connection, student_id)
        result["skill_ids"] = list(
            connection.execute(
                select(student_skills.c.skill_id).where(
                    student_skills.c.student_id == student_id
                )
            ).scalars()
        )
        return result


def list_students() -> list[dict]:
    with engine.connect() as connection:
        rows = connection.execute(
            select(students).order_by(students.c.student_id)
        ).mappings()
        results = []
        for row in rows:
            item = dict(row)
            item["skills"] = _skill_names(connection, row.student_id)
            item["skill_ids"] = list(
                connection.execute(
                    select(student_skills.c.skill_id).where(
                        student_skills.c.student_id == row.student_id
                    )
                ).scalars()
            )
            results.append(item)
        return results


def _replace_student_skills(
    connection, student_id: int, skill_ids: Sequence[int]
) -> None:
    connection.execute(
        delete(student_skills).where(student_skills.c.student_id == student_id)
    )
    if skill_ids:
        existing = set(
            connection.execute(
                select(skills.c.skill_id).where(skills.c.skill_id.in_(skill_ids))
            ).scalars()
        )
        missing = set(skill_ids) - existing
        if missing:
            raise ValueError(f"Unknown skill IDs: {sorted(missing)}")
        connection.execute(
            insert(student_skills),
            [
                {"student_id": student_id, "skill_id": skill_id}
                for skill_id in set(skill_ids)
            ],
        )


def create_student(payload: dict) -> dict:
    values = {key: value for key, value in payload.items() if key != "skill_ids"}
    with engine.begin() as connection:
        student_id = connection.execute(
            insert(students).returning(students.c.student_id), values
        ).scalar_one()
        _replace_student_skills(connection, student_id, payload["skill_ids"])
    return student_with_skills(student_id)  # type: ignore[return-value]


def update_student(student_id: int, payload: dict) -> dict | None:
    values = {key: value for key, value in payload.items() if key != "skill_ids"}
    with engine.begin() as connection:
        result = connection.execute(
            update(students).where(students.c.student_id == student_id).values(**values)
        )
        if result.rowcount == 0:
            return None
        _replace_student_skills(connection, student_id, payload["skill_ids"])
    return student_with_skills(student_id)


def list_courses() -> list[dict]:
    with engine.connect() as connection:
        return [
            dict(row)
            for row in connection.execute(
                select(courses).order_by(courses.c.course_id)
            ).mappings()
        ]


def create_course(payload: dict, embedding: bytes) -> dict:
    with engine.begin() as connection:
        course_id = connection.execute(
            insert(courses).returning(courses.c.course_id), payload
        ).scalar_one()
        connection.execute(
            insert(course_embeddings).values(course_id=course_id, embedding=embedding)
        )
    return {"course_id": course_id, **payload}


def list_skills() -> list[dict]:
    with engine.connect() as connection:
        return [
            dict(row)
            for row in connection.execute(
                select(skills).order_by(skills.c.category, skills.c.skill_name)
            ).mappings()
        ]


def create_skill(payload: dict) -> dict:
    with engine.begin() as connection:
        skill_id = connection.execute(
            insert(skills).returning(skills.c.skill_id), payload
        ).scalar_one()
    return {"skill_id": skill_id, **payload}


def create_prediction_history(
    student_id: int,
    risk_level: str,
    risk_score: float,
    indicators: list[str],
    features: dict,
) -> None:
    with engine.begin() as connection:
        connection.execute(
            insert(prediction_history).values(
                student_id=student_id,
                risk_level=risk_level,
                risk_score=risk_score,
                academic_indicators=indicators,
                feature_snapshot=features,
            )
        )


def prediction_history_for_student(student_id: int) -> list[dict]:
    with engine.connect() as connection:
        statement = (
            select(prediction_history)
            .where(prediction_history.c.student_id == student_id)
            .order_by(
                prediction_history.c.created_at.desc(), prediction_history.c.id.desc()
            )
        )
        events = [dict(row) for row in connection.execute(statement).mappings()]
    current_student = None
    for event in events:
        if event["academic_indicators"] is None:
            current_student = current_student or student_with_skills(student_id)
            event["academic_indicators"] = (
                academic_indicators(current_student) if current_student else []
            )
            event["indicators_source"] = "current_profile"
        else:
            event["indicators_source"] = "recorded"
    return events


def log_recommendations(
    student_id: int, recommendations: list[dict], guidance: str | None = None
) -> None:
    with engine.begin() as connection:
        connection.execute(
            insert(recommendation_logs).values(
                student_id=student_id,
                recommended_course_ids=[item["course_id"] for item in recommendations],
                recommendations=recommendations,
                academic_guidance=guidance,
            )
        )


def recommendation_history_for_student(student_id: int) -> list[dict]:
    with engine.connect() as connection:
        statement = (
            select(recommendation_logs)
            .where(recommendation_logs.c.student_id == student_id)
            .order_by(
                recommendation_logs.c.created_at.desc(), recommendation_logs.c.id.desc()
            )
        )
        events = [dict(row) for row in connection.execute(statement).mappings()]
        legacy_ids = {
            course_id
            for event in events
            if event["recommendations"] is None
            for course_id in event["recommended_course_ids"]
        }
        titles = (
            dict(
                connection.execute(
                    select(courses.c.course_id, courses.c.title).where(
                        courses.c.course_id.in_(legacy_ids)
                    )
                ).all()
            )
            if legacy_ids
            else {}
        )
    for event in events:
        if event["recommendations"] is None:
            event["recommendations"] = [
                {
                    "course_id": course_id,
                    "course_title": titles.get(course_id, f"Course {course_id}"),
                    "similarity_score": None,
                    "match_percentage": None,
                    "relevant_skills": [],
                    "explanation": "Older recommendation: original scores and explanations were not recorded.",
                }
                for course_id in event["recommended_course_ids"]
            ]
            event["details_source"] = "legacy_course_lookup"
        else:
            event["details_source"] = "recorded"
    return events


def dashboard_stats() -> dict:
    with engine.connect() as connection:
        student_count = connection.execute(select(students.c.student_id)).all()
        course_count = connection.execute(select(courses.c.course_id)).all()
        latest_predictions = (
            connection.execute(select(prediction_history.c.risk_level)).scalars().all()
        )
    return {
        "students": len(student_count),
        "courses": len(course_count),
        "high_risk_predictions": sum(
            level == "High Risk" for level in latest_predictions
        ),
    }
