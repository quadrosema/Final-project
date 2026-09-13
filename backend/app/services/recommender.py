"""Sentence-transformer embeddings and cosine-similarity course ranking."""

from functools import lru_cache

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import insert, select

from app.database import engine
from app.tables import course_embeddings, courses

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


def _embedding_bytes(embedding: np.ndarray) -> bytes:
    return embedding.astype(np.float32).tobytes()


def _embedding_from_bytes(raw: bytes) -> np.ndarray:
    return np.frombuffer(raw, dtype=np.float32)


def generate_course_embedding(description: str) -> bytes:
    vector = embedding_model().encode(description, normalize_embeddings=True)
    return _embedding_bytes(np.asarray(vector))


def store_course_embedding(course_id: int, description: str) -> None:
    embedding = generate_course_embedding(description)
    with engine.begin() as connection:
        connection.execute(
            course_embeddings.delete().where(course_embeddings.c.course_id == course_id)
        )
        connection.execute(
            insert(course_embeddings).values(course_id=course_id, embedding=embedding)
        )


def recommend_for_student(student: dict, top_n: int = 3) -> list[dict]:
    profile = " ".join(
        [student["major"], student.get("interests", ""), *student["skills"]]
    ).strip()
    student_vector = np.asarray(
        embedding_model().encode(profile, normalize_embeddings=True)
    )
    with engine.connect() as connection:
        rows = (
            connection.execute(
                select(courses, course_embeddings.c.embedding).join(
                    course_embeddings,
                    courses.c.course_id == course_embeddings.c.course_id,
                )
            )
            .mappings()
            .all()
        )
    if len(rows) < top_n:
        raise ValueError(
            f"At least {top_n} courses with embeddings are required for recommendations."
        )

    scored = []
    for row in rows:
        similarity = float(
            cosine_similarity([student_vector], [_embedding_from_bytes(row.embedding)])[
                0
            ][0]
        )
        text = f"{row.title} {row.description}".lower()
        relevant_skills = [
            skill for skill in student["skills"] if skill.lower() in text
        ]
        evidence = (
            ", ".join(relevant_skills)
            if relevant_skills
            else "your stated interests and academic profile"
        )
        scored.append(
            {
                "course_id": row.course_id,
                "course_title": row.title,
                "similarity_score": round(similarity, 4),
                "match_percentage": round(max(0.0, similarity) * 100, 2),
                "relevant_skills": relevant_skills,
                "explanation": f"Recommended because {evidence} match the course description.",
            }
        )
    return sorted(scored, key=lambda item: item["similarity_score"], reverse=True)[
        :top_n
    ]
