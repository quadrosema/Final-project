# Dataset provenance and limits

This is a **synthetic demonstration dataset**, not collected student records.
The included `ml/generate_dataset.py` produces 360 rows with NumPy seed 42.
Features are GPA (1–4), attendance (45–100%), failed credits (integer 0–12),
and assignment completion (40–100%).

The generator assigns labels using:

```text
points = (2.3 - GPA) * 2 + (75 - attendance) / 20
         + failed_credits / 3 + (70 - assignment_completion) / 25
High Risk: points >= 3; Medium Risk: points >= 1; otherwise Low Risk.
```

The offline training script inspects columns, missing values, feature statistics,
and class counts; normalizes numeric values and labels; removes invalid/out-of-range
rows and exact duplicates; and writes `academic_risk_dataset_cleaned.csv`.
It does not overwrite the source dataset. Clean data is split into 270 training
and 90 held-out test rows, stratified by label with seed 42.

Accuracy measures reproduction of the synthetic labeling rule. It is not
evidence of performance on real student outcomes. Predictions are decision-support
demonstrations, not a validated academic policy. The displayed risk score is
confidence in the predicted class, not the probability of failure.
