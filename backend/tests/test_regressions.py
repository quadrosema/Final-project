"""Regression tests. Database writes are rolled back after each test."""

import unittest
from contextlib import contextmanager
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError

from app.database import engine
from app.main import app
from app.services import repository
from app.tables import courses, prediction_history, recommendation_logs
from ml.train_model import clean_dataset


class TransactionEngine:
    def __init__(self, connection):
        self.connection = connection

    @contextmanager
    def connect(self):
        yield self.connection

    @contextmanager
    def begin(self):
        with self.connection.begin_nested():
            yield self.connection


class RegressionTests(unittest.TestCase):
    def setUp(self):
        self.connection = engine.connect()
        self.transaction = self.connection.begin()
        self.patch = patch.object(
            repository, "engine", TransactionEngine(self.connection)
        )
        self.patch.start()
        self.client = TestClient(app)
        self.payload = {
            "name": "Regression fixture",
            "major": "Computer Science",
            "academic_year": "Third Year",
            "gpa": 2.4,
            "attendance_rate": 76,
            "assignment_completion_rate": 72,
            "failed_credits": 3,
            "interests": "Machine learning",
            "skill_ids": [],
        }
        self.student_id = repository.create_student(self.payload)["student_id"]
        repository.create_course(
            {
                "title": "Regression course",
                "code": f"TEST-FIXTURE-{self.student_id}",
                "department": "Computer Science",
                "description": "Python",
                "credits": 3,
            },
            b"test-only embedding; rolled back with the fixture",
        )

    def tearDown(self):
        self.patch.stop()
        self.transaction.rollback()
        self.connection.close()

    def test_anonymous_prediction_is_rejected(self):
        response = self.client.post(
            "/api/predict-risk",
            json={
                key: self.payload[key]
                for key in (
                    "gpa",
                    "attendance_rate",
                    "assignment_completion_rate",
                    "failed_credits",
                )
            },
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("student_id", str(response.json()))

    def test_prediction_snapshot_survives_profile_edit(self):
        response = self.client.post(
            "/api/predict-risk", json={"student_id": self.student_id, "gpa": 1.5}
        )
        self.assertEqual(response.status_code, 200)
        original = response.json()
        repository.update_student(
            self.student_id, {**self.payload, "gpa": 4, "failed_credits": 0}
        )
        dashboard = self.client.get(f"/api/dashboard/student/{self.student_id}").json()
        saved = dashboard["latest_prediction"]
        self.assertEqual(saved["academic_indicators"], original["academic_indicators"])
        self.assertEqual(saved["feature_snapshot"]["gpa"], 1.5)
        self.assertEqual(saved["indicators_source"], "recorded")
        self.assertEqual(len(dashboard["prediction_history"]), 1)

    def test_recommendation_and_guidance_survive_dashboard_reload(self):
        course_id = repository.list_courses()[0]["course_id"]
        snapshots = [
            {
                "course_id": course_id,
                "course_title": "Historical title",
                "similarity_score": 0.81,
                "match_percentage": 81.0,
                "relevant_skills": ["Python"],
                "explanation": "Historical explanation.",
            }
        ]
        with patch(
            "app.main.recommender.recommend_for_student", return_value=snapshots
        ):
            response = self.client.post(
                "/api/advisor/run", json={"student_id": self.student_id}
            )
        self.assertEqual(response.status_code, 200)
        dashboard = self.client.get(f"/api/dashboard/student/{self.student_id}").json()
        self.assertEqual(dashboard["recommendations"], snapshots)
        self.assertEqual(
            dashboard["academic_guidance"], response.json()["academic_guidance"]
        )
        self.assertEqual(
            dashboard["recommendation_history"][0]["details_source"], "recorded"
        )

    def test_recommend_endpoint_records_full_details(self):
        course_id = repository.list_courses()[0]["course_id"]
        snapshot = {
            "course_id": course_id,
            "course_title": "Python",
            "similarity_score": 0.5,
            "match_percentage": 50,
            "relevant_skills": [],
            "explanation": "Profile match",
        }
        with patch(
            "app.main.recommender.recommend_for_student", return_value=[snapshot]
        ):
            response = self.client.post(
                "/api/recommend", json={"student_id": self.student_id}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            repository.recommendation_history_for_student(self.student_id)[0][
                "recommendations"
            ],
            [snapshot],
        )

    def test_legacy_history_is_readable_without_invented_scores(self):
        course = repository.list_courses()[0]
        self.connection.execute(
            insert(recommendation_logs).values(
                student_id=self.student_id, recommended_course_ids=[course["course_id"]]
            )
        )
        self.connection.execute(
            insert(prediction_history).values(
                student_id=self.student_id, risk_level="Low Risk", risk_score=64.85
            )
        )
        event = repository.recommendation_history_for_student(self.student_id)[0]
        self.assertEqual(event["recommendations"][0]["course_title"], course["title"])
        self.assertIsNone(event["recommendations"][0]["similarity_score"])
        self.assertEqual(
            repository.prediction_history_for_student(self.student_id)[0][
                "indicators_source"
            ],
            "current_profile",
        )

    def test_embedding_failure_does_not_save_course(self):
        payload = {
            "title": "Unsaved fixture",
            "code": "TEST-EMBED-FAIL",
            "department": "Computer Science",
            "description": "Python",
            "credits": 3,
        }
        with patch(
            "app.main.recommender.generate_course_embedding",
            side_effect=RuntimeError("Test download failure"),
        ):
            response = self.client.post("/api/courses", json=payload)
        self.assertEqual(response.status_code, 503)
        self.assertIsNone(
            self.connection.execute(
                select(courses).where(courses.c.code == payload["code"])
            ).first()
        )

    def test_embedding_insert_failure_rolls_back_course_insert(self):
        payload = {
            "title": "Atomic fixture",
            "code": "TEST-ATOMIC",
            "department": "Computer Science",
            "description": "Python",
            "credits": 3,
        }
        with self.assertRaises(IntegrityError):
            repository.create_course(payload, None)
        self.assertIsNone(
            self.connection.execute(
                select(courses).where(courses.c.code == payload["code"])
            ).first()
        )

    def test_create_second_student_preserves_first(self):
        response = self.client.post(
            "/api/students", json={**self.payload, "name": "Second fixture"}
        )
        self.assertEqual(response.status_code, 201)
        self.assertNotEqual(response.json()["student_id"], self.student_id)
        self.assertEqual(
            repository.student_with_skills(self.student_id)["name"],
            self.payload["name"],
        )


class CleaningTests(unittest.TestCase):
    def test_dirty_rows_are_removed_and_labels_normalized(self):
        clean_rows = [
            {
                "gpa": 1 + index / 10,
                "attendance_rate": 70,
                "failed_credits": 3,
                "assignment_completion_rate": 80,
                "risk_level": label,
            }
            for label in ("Low Risk", "Medium Risk", "High Risk")
            for index in range(4)
        ]
        raw = pd.DataFrame(
            clean_rows
            + [
                clean_rows[0],
                {**clean_rows[1], "gpa": "invalid"},
                {**clean_rows[2], "failed_credits": 2.5},
                {**clean_rows[3], "attendance_rate": 101},
            ]
        )
        raw.loc[0, "risk_level"] = " Low Risk "
        cleaned, report = clean_dataset(raw)
        self.assertEqual(len(cleaned), 12)
        self.assertEqual(report["invalid_rows_removed"], 3)
        self.assertEqual(report["duplicate_rows_removed"], 1)
        self.assertEqual(cleaned.loc[0, "risk_level"], "Low Risk")


if __name__ == "__main__":
    unittest.main()
