"""Clean, inspect, train, evaluate, and save the academic-risk classifier offline."""

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
from app.ml.risk_model import FEATURE_NAMES

DATASET_PATH = BACKEND_DIR / "data" / "academic_risk_dataset.csv"
MODEL_PATH = BACKEND_DIR / "models" / "academic_risk_model.joblib"


def clean_dataset(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    required = FEATURE_NAMES + ["risk_level"]
    missing = set(required) - set(raw.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    data = raw[required].copy()
    original_missing = int(data.isna().any(axis=1).sum())
    for name in FEATURE_NAMES:
        data[name] = pd.to_numeric(data[name], errors="coerce")
    data["risk_level"] = data["risk_level"].astype("string").str.strip()
    data = data.replace([np.inf, -np.inf], np.nan)
    invalid = (
        data.isna().any(axis=1)
        | ~data["gpa"].between(0, 4)
        | ~data["attendance_rate"].between(0, 100)
        | ~data["assignment_completion_rate"].between(0, 100)
        | (data["failed_credits"] < 0)
        | (data["failed_credits"] % 1 != 0)
        | ~data["risk_level"].isin(["Low Risk", "Medium Risk", "High Risk"])
    )
    invalid_count = int(invalid.sum())
    data = data.loc[~invalid].copy()
    duplicates = int(data.duplicated().sum())
    data = data.drop_duplicates().reset_index(drop=True)
    data["failed_credits"] = data["failed_credits"].astype(int)
    counts = data["risk_level"].value_counts()
    if len(counts) != 3 or counts.min() < 4:
        raise ValueError(
            "Provide all three risk classes with at least four clean rows each."
        )
    inspection = {
        "source_rows": len(raw),
        "source_rows_with_missing_values": original_missing,
        "invalid_rows_removed": invalid_count,
        "duplicate_rows_removed": duplicates,
        "clean_rows": len(data),
        "features": FEATURE_NAMES,
        "class_counts": {str(label): int(count) for label, count in counts.items()},
        "feature_statistics": data[FEATURE_NAMES].describe().to_dict(),
    }
    return data, inspection


def main() -> None:
    if not DATASET_PATH.exists():
        raise FileNotFoundError("Run python ml/generate_dataset.py before training.")
    dataset, inspection = clean_dataset(pd.read_csv(DATASET_PATH))
    dataset.to_csv(
        BACKEND_DIR / "data" / "academic_risk_dataset_cleaned.csv", index=False
    )
    print("Dataset inspection and cleaning:")
    print(json.dumps(inspection, indent=2))
    x_train, x_test, y_train, y_test = train_test_split(
        dataset[FEATURE_NAMES],
        dataset["risk_level"],
        test_size=0.25,
        random_state=42,
        stratify=dataset["risk_level"],
    )
    model = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(max_iter=2000, random_state=42)),
        ]
    )
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    metrics = {
        "accuracy": accuracy_score(y_test, predictions),
        "precision_weighted": precision_score(
            y_test, predictions, average="weighted", zero_division=0
        ),
        "recall_weighted": recall_score(
            y_test, predictions, average="weighted", zero_division=0
        ),
        "f1_weighted": f1_score(
            y_test, predictions, average="weighted", zero_division=0
        ),
    }
    classes = list(model.classes_)
    matrix = confusion_matrix(y_test, predictions, labels=classes)
    report = classification_report(
        y_test, predictions, labels=classes, output_dict=True, zero_division=0
    )
    correct = int((y_test.to_numpy() == predictions).sum())
    interpretation = [
        f"The classifier assigned {correct}/{len(y_test)} held-out labels correctly ({metrics['accuracy']:.2%}); {len(y_test) - correct} were incorrect.",
        "Weighted precision measures correctness of assigned labels, recall measures recovered true labels, and F1 balances the two, weighted by class support.",
    ]
    for index, label in enumerate(classes):
        support = int(matrix[index].sum())
        assigned = int(matrix[:, index].sum())
        interpretation.append(
            f"{label}: correctly recovered {matrix[index, index]}/{support} true cases (recall {report[label]['recall']:.2%}); {matrix[index, index]}/{assigned} assigned labels were correct (precision {report[label]['precision']:.2%})."
        )
        for column, predicted_label in enumerate(classes):
            if column != index and matrix[index, column]:
                interpretation.append(
                    f"{matrix[index, column]} true {label} case(s) were predicted as {predicted_label}."
                )
    interpretation.append(
        "LIMITATION: these are synthetic profiles labeled by the generator's hand-written risk formula, not observed student outcomes. High test accuracy shows reproduction of that formula; it does not establish real-world advising accuracy or calibrated failure probabilities."
    )
    print("Evaluation metrics:")
    print(json.dumps(metrics, indent=2))
    print(f"Confusion matrix (true rows, predicted columns; order {classes}):")
    print(matrix)
    print("Classification report:")
    print(classification_report(y_test, predictions, labels=classes, zero_division=0))
    print("Result explanation:")
    print("\n".join(interpretation))
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    evaluation = {
        "dataset_source": "Synthetic; ml/generate_dataset.py, seed 42",
        "inspection": inspection,
        "train_rows": len(x_train),
        "test_rows": len(x_test),
        "random_state": 42,
        "metrics": metrics,
        "class_order": classes,
        "confusion_matrix": matrix.tolist(),
        "classification_report": report,
        "interpretation": interpretation,
    }
    (MODEL_PATH.parent / "evaluation.json").write_text(
        json.dumps(evaluation, indent=2), encoding="utf-8"
    )
    print(f"Saved trained model: {MODEL_PATH}")


if __name__ == "__main__":
    main()
