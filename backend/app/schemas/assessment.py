from typing import List

from pydantic import BaseModel


# ------------------------
# Generate Assessment
# ------------------------

class GenerateAssessmentRequest(
    BaseModel
):
    chapter_id: str
    difficulty: str
    num_questions: int


class QuestionResponse(
    BaseModel
):
    question_id: str
    question_text: str
    marks: int
    difficulty: str


class GenerateAssessmentResponse(
    BaseModel
):
    assessment_id: str
    chapter_id: str
    difficulty: str
    total_questions: int
    total_marks: int
    questions: List[
        QuestionResponse
    ]


# ------------------------
# Submit Assessment
# ------------------------

class StudentAnswer(
    BaseModel
):
    question_id: str
    answer: str


class SubmitAssessmentRequest(
    BaseModel
):
    assessment_id: str
    answers: List[
        StudentAnswer
    ]


class QuestionResult(
    BaseModel
):
    question_id: str
    question_text: str

    score: int
    max_score: int

    semantic_similarity: float
    rubric_coverage: float

    feedback: str

    matched_points: List[str]
    missing_points: List[str]


class SubmitAssessmentResponse(
    BaseModel
):
    assessment_id: str

    total_questions: int

    total_score: int

    max_score: int

    percentage: float

    results: List[
        QuestionResult
    ]