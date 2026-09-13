import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/academic_advisor",
)
MODEL_PATH = Path(
    os.getenv("MODEL_PATH", str(BASE_DIR / "models/academic_risk_model.joblib"))
)
