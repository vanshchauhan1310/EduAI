from pydantic import BaseModel


class StudentInput(BaseModel):

    gender: str
    age: int
    class_level: int

    attendance_pct: float
    avg_marks: float

    previous_failures: int

    family_income_monthly: float

    distance_to_school_km: float

    guardian_education: str

    single_parent: int

    sibling_dropout: int

    mobile_available: int

    internet_access: int

    scholarship: int

    midday_meal: int

    study_hours_per_day: float

    health_risk: str

    school_engagement_score: float

    teacher_feedback_score: float

    disciplinary_incidents: int


class PredictionResponse(BaseModel):

    dropout_probability: float

    risk_level: str

    recommended_action: str