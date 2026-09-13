# AI-Powered Student Success & Academic Advisor

A graduation project that manages student profiles, predicts academic risk, recommends courses based on skills and interests, and provides personalized academic guidance.

## Features and architecture

- Student profile forms, search, performance cards, and skills display.
- Course and skill management through the API.
- Low/Medium/High Risk prediction and three ranked course recommendations.
- Academic guidance, match explanations, and persistent prediction/recommendation history.

```text
React dashboard -> FastAPI -> PostgreSQL (SQLAlchemy Core + Alembic)
                         -> Saved Logistic Regression model
                         -> MiniLM embeddings + cosine similarity
                         -> Three-node LangGraph advisor
```

The database uses SQLAlchemy Core, not ORM. React uses reusable functional components, props, state, effects, forms, and Fetch integration.

## First-time setup

Use Windows PowerShell from the project root. Install Python, Node.js with npm, and PostgreSQL; keep PostgreSQL running.

### 1. Install dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm install --prefix frontend
```

### 2. Configure PostgreSQL

In pgAdmin's Query Tool, connected to the `postgres` database, run once:

```sql
CREATE DATABASE academic_advisor;
```

Create `backend/.env` containing:

```dotenv
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/academic_advisor
MODEL_PATH=models/academic_risk_model.joblib
```

Replace `YOUR_PASSWORD` with your PostgreSQL password. URL-encode special characters in it, such as `@` as `%40`. Never commit `.env`.

### 3. Apply migrations

```powershell
cd backend
..\.venv\Scripts\alembic.exe upgrade head
```

The eight tables are `students`, `courses`, `skills`, `student_skills`, `student_courses`, `course_embeddings`, `prediction_history`, and `recommendation_logs`.

Three migrations create the schema, add interests, and preserve historical snapshots. Alembic is connected to the SQLAlchemy Core metadata.

## How to run

After first-time setup, open **two terminals**, both starting in the project root. Do not recreate the database, overwrite `.env`, or retrain the model each time.

**Terminal 1 - backend**

```powershell
cd backend
..\.venv\Scripts\uvicorn.exe app.main:app --reload
```

Wait for `Application startup complete.`

**Terminal 2 - frontend**

```powershell
cd frontend
npm run dev -- --port 5173 --strictPort
```

If npm is unavailable on PATH but you are using this Codex workspace's bundled Node.js, use this instead from `frontend/`:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe" node_modules/vite/bin/vite.js --port 5173 --strictPort
```

Open the [dashboard](http://localhost:5173/) and [interactive API documentation](http://localhost:8000/docs). Keep both terminals running; press **Ctrl+C** in each to stop the servers.

For an empty database, add skills and **at least three courses** through the API documentation. Create a student in the dashboard, select skills, save, and click **Run academic advisor**. **New student** creates a separate profile.

Course and embedding inserts are atomic: embedding failures do not leave incomplete courses. The first MiniLM download needs internet access. History survives refresh; older records label missing historical details.

## Machine learning

Offline training cleans and inspects GPA, attendance, failed credits, assignment completion, and risk labels, then fits scaled Logistic Regression using a stratified 270/90 train/test split, seed 42.

The included `backend/models/academic_risk_model.joblib` is loaded for predictions, **never trained on startup**. To regenerate data and retrain, run from `backend/`:

```powershell
..\.venv\Scripts\python.exe ml/generate_dataset.py
..\.venv\Scripts\python.exe ml/train_model.py
```

`backend/models/evaluation.json` contains accuracy, precision, recall, F1, confusion matrix, classification report, and explanations. Accuracy is **96.67% (87/90 correct)**; weighted precision/recall/F1 are **96.66%/96.67%/96.64%**. One Low Risk and two Medium Risk cases are misclassified; all 27 High Risk cases are recovered.

The dataset is **synthetic**, not real student outcomes; accuracy measures its labeling rule, not validated real-world performance. Risk score means class confidence, not failure probability. See `backend/data/README.md` for provenance.

## Recommendations and LangGraph

`sentence-transformers/all-MiniLM-L6-v2` embeds course descriptions and the student's skills, interests, and major. Cosine similarity ranks courses; the Top 3 include course titles, similarity scores, match percentages, relevant skills, and explanations.

The LangGraph workflow follows:

```text
Risk Analyzer -> Skill & Course Analyzer -> Academic Advisor
```

The nodes interpret risk, identify learning opportunities, and combine them into actionable, rule-based guidance. No external LLM key is required.

## API reference

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET / POST | `/api/students` | List / create students |
| GET / PUT | `/api/students/{student_id}` | Retrieve / update a student |
| GET / POST | `/api/courses` | List / create courses |
| GET / POST | `/api/skills` | List / create skills |
| POST | `/api/predict-risk` | Predict risk and save the result |
| POST | `/api/recommend` | Rank courses and save recommendations |
| POST | `/api/advisor/run` | Run the complete advisor workflow |
| GET | `/api/dashboard/student/{student_id}` | Profile, latest results, and history |
| GET | `/api/students/{student_id}/recommendations` | Recommendation history |
| GET | `/api/students/{student_id}/prediction-history` | Prediction history |
| GET | `/api/dashboard/stats` | Student, course, and high-risk prediction counts |

Example `POST /api/students` input:

```json
{
  "name": "Amina Saleh",
  "major": "Computer Science",
  "academic_year": "Third Year",
  "gpa": 2.4,
  "attendance_rate": 76,
  "assignment_completion_rate": 72,
  "failed_credits": 3,
  "interests": "Machine learning and data analysis",
  "skill_ids": []
}
```

Use existing skill IDs to associate skills. Send `{"student_id": 1}` to prediction, recommendation, or advisor endpoints, using the actual student ID. Predictions accept optional feature overrides and record those inputs.

Example prediction response for the profile above:

```json
{
  "student_id": 1,
  "risk_level": "Low Risk",
  "risk_score": 64.85,
  "academic_indicators": ["3 failed credits recorded"]
}
```

Pydantic validates inputs. Invalid/missing data returns **422**, unknown students **404**, duplicate course codes or skills **409**, and unavailable database/embedding services **503**.

## Quality checks

Run from `backend/`:

```powershell
..\.venv\Scripts\ruff.exe check .
..\.venv\Scripts\ruff.exe format .
..\.venv\Scripts\python.exe -m unittest discover -s tests -v
..\.venv\Scripts\alembic.exe check
```

Tests roll back their database writes. Run `npm run build` from `frontend/` for the production build.

Source, schema, migrations, training code, datasets, saved model, evaluation, and `requirements.txt` are included. GitHub publishing is pending.
