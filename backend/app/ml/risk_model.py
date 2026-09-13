from pathlib import Path

import joblib
import pandas as pd

from app.config import MODEL_PATH

FEATURE_NAMES = [
    "gpa",
    "attendance_rate",
    "failed_credits",
    "assignment_completion_rate",
]


def load_risk_model(model_path: Path = MODEL_PATH):
    if not model_path.exists():
        raise FileNotFoundError(
            f"Saved model was not found at {model_path}. Run backend/ml/train_model.py first."
        )
    return joblib.load(model_path)


def academic_indicators(features: dict) -> list[str]:
    indicators = []
    if features["gpa"] < 2.0:
        indicators.append("GPA is below 2.0")
    if features["attendance_rate"] < 75:
        indicators.append("Attendance rate is below 75%")
    if features["failed_credits"] > 0:
        indicators.append(f"{features['failed_credits']} failed credits recorded")
    if features["assignment_completion_rate"] < 70:
        indicators.append("Assignment completion rate is below 70%")
    return indicators or ["Academic indicators are currently within the expected range"]


def predict_risk(features: dict) -> tuple[str, float, list[str]]:
    model = load_risk_model()
    values = pd.DataFrame(
        [[features[name] for name in FEATURE_NAMES]], columns=FEATURE_NAMES
    )
    level = str(model.predict(values)[0])
    probabilities = dict(
        zip(model.classes_, model.predict_proba(values)[0], strict=True)
    )
    score = round(float(probabilities[level]) * 100, 2)
    return level, score, academic_indicators(features)
