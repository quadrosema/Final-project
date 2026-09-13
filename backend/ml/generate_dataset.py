"""Create the reproducible training/testing dataset used by train_model.py."""

from pathlib import Path

import numpy as np
import pandas as pd

OUTPUT = Path(__file__).resolve().parents[1] / "data" / "academic_risk_dataset.csv"


def main() -> None:
    rng = np.random.default_rng(42)
    rows = []
    for _ in range(360):
        gpa = round(float(rng.uniform(1.0, 4.0)), 2)
        attendance = round(float(rng.uniform(45, 100)), 1)
        failed_credits = int(rng.integers(0, 13))
        completion = round(float(rng.uniform(40, 100)), 1)
        risk_points = (
            (2.3 - gpa) * 2
            + (75 - attendance) / 20
            + failed_credits / 3
            + (70 - completion) / 25
        )
        if risk_points >= 3:
            risk_level = "High Risk"
        elif risk_points >= 1:
            risk_level = "Medium Risk"
        else:
            risk_level = "Low Risk"
        rows.append(
            {
                "gpa": gpa,
                "attendance_rate": attendance,
                "failed_credits": failed_credits,
                "assignment_completion_rate": completion,
                "risk_level": risk_level,
            }
        )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUTPUT, index=False)
    print(f"Created {OUTPUT} with {len(rows)} records.")


if __name__ == "__main__":
    main()
