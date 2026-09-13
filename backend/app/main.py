import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.ml.risk_model import predict_risk
from app.schemas import (
    AdvisorResponse,
    CourseCreate,
    CourseOut,
    PredictionRequest,
    RecommendationResponse,
    RiskPrediction,
    SkillCreate,
    SkillOut,
    StudentCreate,
    StudentOut,
    StudentReference,
    StudentUpdate,
)
from app.services import advisor, recommender, repository

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # The model is trained offline and loaded from its joblib artifact only when predicting.
    yield


app = FastAPI(title="AI-Powered Student Success & Academic Advisor", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(_request, exc):
    logger.error("Database operation failed: %s", type(exc).__name__)
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Database operation unavailable. Check the database connection and migrations."
        },
    )


def get_student_or_404(student_id: int) -> dict:
    student = repository.student_with_skills(student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )
    return student


def risk_for_request(request: PredictionRequest) -> RiskPrediction:
    student = get_student_or_404(request.student_id)
    values = {
        name: getattr(request, name)
        if getattr(request, name) is not None
        else student[name]
        for name in (
            "gpa",
            "attendance_rate",
            "assignment_completion_rate",
            "failed_credits",
        )
    }
    try:
        level, score, indicators = predict_risk(values)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail="Saved risk model not found. Run the offline training script.",
        ) from exc
    repository.create_prediction_history(
        request.student_id, level, score, indicators, values
    )
    return RiskPrediction(
        student_id=request.student_id,
        risk_level=level,
        risk_score=score,
        academic_indicators=indicators,
    )


def recommendations_or_error(student: dict) -> list[dict]:
    try:
        return recommender.recommend_for_student(student, top_n=3)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except SQLAlchemyError:
        raise
    except Exception as exc:
        logger.error("Recommendation generation failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=503,
            detail="Recommendation model unavailable. Check its local cache or download connection.",
        ) from exc


@app.post(
    "/api/students", response_model=StudentOut, status_code=status.HTTP_201_CREATED
)
def create_student(payload: StudentCreate):
    try:
        return repository.create_student(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Student could not be created"
        ) from exc


@app.get("/api/students", response_model=list[StudentOut])
def get_students():
    return repository.list_students()


@app.get("/api/students/{student_id}", response_model=StudentOut)
def get_student(student_id: int):
    return get_student_or_404(student_id)


@app.put("/api/students/{student_id}", response_model=StudentOut)
def put_student(student_id: int, payload: StudentUpdate):
    try:
        updated = repository.update_student(student_id, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )
    return updated


@app.get("/api/courses", response_model=list[CourseOut])
def get_courses():
    return repository.list_courses()


@app.post("/api/courses", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def post_course(payload: CourseCreate):
    try:
        embedding = recommender.generate_course_embedding(payload.description)
    except Exception as exc:
        logger.error("Course embedding failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=503,
            detail="Course embedding could not be generated. No course was saved.",
        ) from exc
    try:
        return repository.create_course(payload.model_dump(), embedding)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Course code already exists"
        ) from exc


@app.get("/api/skills", response_model=list[SkillOut])
def get_skills():
    return repository.list_skills()


@app.post("/api/skills", response_model=SkillOut, status_code=status.HTTP_201_CREATED)
def post_skill(payload: SkillCreate):
    try:
        return repository.create_skill(payload.model_dump())
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Skill already exists"
        ) from exc


@app.post("/api/predict-risk", response_model=RiskPrediction)
def post_predict_risk(payload: PredictionRequest):
    return risk_for_request(payload)


@app.post("/api/recommend", response_model=RecommendationResponse)
def post_recommend(payload: StudentReference):
    student = get_student_or_404(payload.student_id)
    recommendations = recommendations_or_error(student)
    repository.log_recommendations(payload.student_id, recommendations)
    return {"student_id": payload.student_id, "recommendations": recommendations}


@app.post("/api/advisor/run", response_model=AdvisorResponse)
def post_advisor_run(payload: StudentReference):
    student = get_student_or_404(payload.student_id)
    risk = risk_for_request(PredictionRequest(student_id=payload.student_id))
    recommendations = recommendations_or_error(student)
    final_state = advisor.build_advisor_graph().invoke(
        {
            "student": student,
            "risk": risk.model_dump(),
            "recommendations": recommendations,
        }
    )
    repository.log_recommendations(
        payload.student_id, recommendations, final_state["academic_guidance"]
    )
    return {
        "student_id": payload.student_id,
        "risk": risk,
        "recommendations": recommendations,
        "academic_guidance": final_state["academic_guidance"],
    }


@app.get("/api/dashboard/student/{student_id}")
def get_student_dashboard(student_id: int):
    student = get_student_or_404(student_id)
    predictions = repository.prediction_history_for_student(student_id)
    recommendations = repository.recommendation_history_for_student(student_id)
    return {
        "student": student,
        "latest_prediction": predictions[0] if predictions else None,
        "prediction_history": predictions,
        "recommendation_history": recommendations,
        "recommendations": recommendations[0]["recommendations"]
        if recommendations
        else [],
        "academic_guidance": recommendations[0]["academic_guidance"]
        if recommendations
        else None,
    }


@app.get("/api/students/{student_id}/recommendations")
def get_recommendation_history(student_id: int):
    get_student_or_404(student_id)
    return repository.recommendation_history_for_student(student_id)


@app.get("/api/students/{student_id}/prediction-history")
def get_prediction_history(student_id: int):
    get_student_or_404(student_id)
    return repository.prediction_history_for_student(student_id)


@app.get("/api/dashboard/stats")
def get_dashboard_stats():
    return repository.dashboard_stats()
