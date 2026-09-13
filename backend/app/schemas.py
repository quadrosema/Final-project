from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StudentBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    major: str = Field(min_length=1, max_length=120)
    academic_year: str = Field(min_length=1, max_length=40)
    gpa: float = Field(ge=0, le=4)
    attendance_rate: float = Field(ge=0, le=100)
    assignment_completion_rate: float = Field(ge=0, le=100)
    failed_credits: int = Field(ge=0)
    interests: str = ""
    skill_ids: list[int] = Field(default_factory=list)


class StudentCreate(StudentBase):
    pass


class StudentUpdate(StudentBase):
    pass


class StudentOut(StudentBase):
    model_config = ConfigDict(from_attributes=True)
    student_id: int
    skills: list[str] = Field(default_factory=list)


class CourseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    code: str = Field(min_length=1, max_length=30)
    department: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1)
    credits: int = Field(ge=1, le=12)


class CourseOut(CourseCreate):
    course_id: int


class SkillCreate(BaseModel):
    skill_name: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=120)


class SkillOut(SkillCreate):
    skill_id: int


class PredictionRequest(BaseModel):
    student_id: int = Field(
        gt=0, description="Required so every prediction is recorded for a student."
    )
    gpa: float | None = Field(default=None, ge=0, le=4)
    attendance_rate: float | None = Field(default=None, ge=0, le=100)
    assignment_completion_rate: float | None = Field(default=None, ge=0, le=100)
    failed_credits: int | None = Field(default=None, ge=0)


class StudentReference(BaseModel):
    student_id: int = Field(gt=0)


class RiskPrediction(BaseModel):
    student_id: int
    risk_level: str
    risk_score: float = Field(
        description="Model confidence in the predicted risk level, from 0 to 100."
    )
    academic_indicators: list[str]


class RecommendationItem(BaseModel):
    course_id: int
    course_title: str
    similarity_score: float
    match_percentage: float
    relevant_skills: list[str]
    explanation: str


class RecommendationResponse(BaseModel):
    student_id: int
    recommendations: list[RecommendationItem]


class AdvisorResponse(BaseModel):
    student_id: int
    risk: RiskPrediction
    recommendations: list[RecommendationItem]
    academic_guidance: str


class HistoryPrediction(BaseModel):
    id: int
    risk_level: str
    risk_score: float
    created_at: datetime
