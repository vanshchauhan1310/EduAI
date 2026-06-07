from pydantic import BaseModel


class EvaluationRequest(
    BaseModel
):
    question_id: str
    student_answer: str


class EvaluationResponse(
    BaseModel
):
    score: int
    max_score: int

    semantic_similarity: float
    rubric_coverage: float

    matched_points: list[str]
    missing_points: list[str]

    feedback: str