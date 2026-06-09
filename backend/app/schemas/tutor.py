from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


# ------------------------
# Shared pieces (mirror mobile types/index.ts 1:1)
# ------------------------

class ConceptImageOut(BaseModel):
    """NEW — "concept images" feature: a CC-licensed educational diagram for a
    concept, sourced from Wikimedia Commons (see app.ai.tutor.image_search)."""
    title: str
    thumbnail_url: str
    full_url: str
    attribution: str
    source_url: str


class StudentAnalysisOut(BaseModel):
    level: str
    strong_concepts: List[str] = []
    weak_concepts: List[str] = []
    misconceptions: List[str] = []


class LearningPathItemOut(BaseModel):
    concept: str
    priority: int
    reason: str
    estimated_time: str
    activity: str


class TutorLessonOut(BaseModel):
    concept: str
    english_explanation: str
    telugu_explanation: str = ""
    real_life_examples: List[str] = []
    worked_examples: List[str] = []
    common_mistakes: List[str] = []
    revision_notes: List[str] = []


class TutorQuizItemOut(BaseModel):
    question: str
    type: str
    difficulty: str
    concept_tested: str = ""
    options: List[str] = []
    answer: str
    explanation: str = ""


class TutorRecommendationsOut(BaseModel):
    next_concepts: List[str] = []
    estimated_mastery_score: float = 0.0
    next_lesson: str = ""


class RagSourceOut(BaseModel):
    kind: str           # 'pdf' | 'note'
    concept: str
    text: str
    score: float
    source: Optional[str] = None


class ConceptMasteryOut(BaseModel):
    subject: str
    chapter: str
    concept: str
    mastery: float
    level: str
    updated_at: Optional[datetime] = None


# ------------------------
# POST /tutor/generate
# ------------------------

class TutorGenerateRequest(BaseModel):
    subject: str
    chapter: str
    concept: str
    mastery: float
    language: str = "both"
    num_questions: int = 10
    question_types: List[str] = ["MCQ"]


class TutorGenerateResponse(BaseModel):
    student_analysis: StudentAnalysisOut
    learning_path: List[LearningPathItemOut] = []
    lesson: TutorLessonOut
    quiz: List[TutorQuizItemOut] = []
    recommendations: TutorRecommendationsOut
    rag_sources: List[RagSourceOut] = []
    mastery: float
    images: List[ConceptImageOut] = []


# ------------------------
# POST /tutor/quiz/grade
# ------------------------

class GradeQuizRequest(BaseModel):
    subject: str
    chapter: str
    concept: str
    mastery: float
    quiz: List[TutorQuizItemOut]
    answers: Dict[int, str] = {}


class QuizGradeResultOut(BaseModel):
    index: int
    question: str
    type: str
    is_correct: Optional[bool] = None
    correct_answer: str
    explanation: str = ""


class QuizGradeResponse(BaseModel):
    correct: int
    scored: int
    percentage: float
    results: List[QuizGradeResultOut] = []
    passed: bool
    message: str
    next_concept: Optional[str] = None
    review_topics: List[str] = []
    old_mastery: float
    new_mastery: float


# ------------------------
# POST /tutor/chat
# ------------------------

class ChatHistoryMessage(BaseModel):
    role: str           # 'user' | 'assistant'
    content: str


class ChatRequest(BaseModel):
    question: str
    language: str = "english"
    history: List[ChatHistoryMessage] = []


class ChatSourceOut(BaseModel):
    kind: str           # 'pdf' | 'note'
    concept: str
    text: str
    score: float


class SuggestedVideoOut(BaseModel):
    """A suggested YouTube video related to the topic."""
    title: str
    channel: str
    url: str


class ChatResponse(BaseModel):
    answer: str
    detected_topic: str
    sources: List[ChatSourceOut] = []
    images: List[ConceptImageOut] = []
    videos: List[SuggestedVideoOut] = []


# ------------------------
# Knowledge base ("My Study Material")
# ------------------------

class KnowledgeBaseSourceOut(BaseModel):
    id: str
    source: str
    subject: str
    chapter: str
    chunks: int
    uploaded_at: datetime


class IngestResultOut(BaseModel):
    success: bool
    source: str
    pages: int
    chunks: int
    error: Optional[str] = None
