"""
Pydantic schemas for the adaptive tutor output (matches the tutor spec).
The LangChain PydanticOutputParser targets `TutorResponse`.
"""

from typing import List, Literal

from pydantic import BaseModel, Field

Level = Literal["Beginner", "Intermediate", "Advanced"]
Difficulty = Literal["Easy", "Medium", "Hard"]
QType = Literal["MCQ", "Short Answer", "Application", "Numerical"]


# ── Step 1: student analysis ──────────────────────────────────────────────────
class StudentAnalysis(BaseModel):
    level: str = Field(description="Beginner | Intermediate | Advanced")
    strong_concepts: List[str] = []
    weak_concepts: List[str] = []
    misconceptions: List[str] = []


# ── Step 2: learning path ─────────────────────────────────────────────────────
class LearningPathItem(BaseModel):
    concept: str
    priority: int = Field(description="1 = highest priority")
    reason: str
    estimated_time: str = Field(description="e.g. '20 min'")
    activity: str


# ── Step 3: lesson (bilingual) ────────────────────────────────────────────────
class Lesson(BaseModel):
    concept: str
    english_explanation: str
    telugu_explanation: str = ""
    real_life_examples: List[str] = []
    worked_examples: List[str] = []
    common_mistakes: List[str] = []
    revision_notes: List[str] = []


# ── Step 4: adaptive quiz ─────────────────────────────────────────────────────
class QuizItem(BaseModel):
    question: str
    type: str = Field(description="MCQ | Short Answer | Application | Numerical")
    difficulty: str = Field(description="Easy | Medium | Hard")
    concept_tested: str = ""
    options: List[str] = Field(
        default_factory=list,
        description="For MCQ: exactly 4 options prefixed 'A) '..'D) '. Empty otherwise.",
    )
    answer: str = Field(description="MCQ: the letter A-D. Else the expected answer.")
    explanation: str = ""


# ── Step 5: recommendations ───────────────────────────────────────────────────
class Recommendations(BaseModel):
    next_concepts: List[str] = []
    estimated_mastery_score: float = 0.0
    next_lesson: str = ""


# ── Full response ─────────────────────────────────────────────────────────────
class TutorResponse(BaseModel):
    student_analysis: StudentAnalysis
    learning_path: List[LearningPathItem] = []
    lesson: Lesson
    quiz: List[QuizItem] = []
    recommendations: Recommendations


# ── Board-style exam questions (matches teammate's exam_prep schema) ──────────
class ExamQuestion(BaseModel):
    """Subjective board-exam question — same fields the teammate's
    QuestionGenerator emits, plus marks/difficulty for paper assembly."""
    question_text: str
    type: str = "Subjective"          # Subjective | Numerical | ...
    difficulty: str = "Medium"        # Easy | Medium | Hard
    marks: int = 3
    concept_tested: str = ""
    sample_answer: str = ""
    expected_points: List[str] = []   # used for (auto)grading subjective answers


class Assessment(BaseModel):
    """An assembled paper — same wrapper shape as AssessmentGenerator returns."""
    assessment_id: str
    chapter_id: str
    difficulty: str
    total_questions: int
    total_marks: int
    questions: List[ExamQuestion]
