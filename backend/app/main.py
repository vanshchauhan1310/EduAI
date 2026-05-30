"""
EduSakhi AI Education Platform — main FastAPI application
========================================================
ONE app that serves both:
  • EduSakhi learning endpoints (RAG tutor, diagnostics, quizzes, analytics)
  • Governance endpoints (auth, schools, attendance)

Run from the backend/ folder:
    uvicorn app.main:app --reload --port 8000

EduSakhi engine classes (which pull in heavy deps like chromadb / sentence-
transformers / huggingface-hub) are imported lazily inside handlers, so the
governance API still boots even if those optional deps aren't installed yet.
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.config import settings
from database.db import get_db, create_tables
from database.models import Student
from governance.routes_auth import router as auth_router
from governance.routes_schools import router as schools_router
from governance.routes_attendance import router as attendance_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("edusakhi")


# ── Lifespan: create tables & folders on startup ──────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs("knowledge_base", exist_ok=True)
    logger.info("EduSakhi platform started — tables ready.")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="EduSakhi adaptive learning + education governance — one integrated backend.",
    lifespan=lifespan,
)

# ── Governance routers (auth, schools, attendance) ────────────────────────────
app.include_router(auth_router,       prefix=settings.API_V1_PREFIX)
app.include_router(schools_router,    prefix=settings.API_V1_PREFIX)
app.include_router(attendance_router, prefix=settings.API_V1_PREFIX)


# ══════════════════════════════════════════════════════════════════════════════
# Pydantic request schemas (EduSakhi learning endpoints)
# ══════════════════════════════════════════════════════════════════════════════
class StudentCreate(BaseModel):
    name: str
    age: Optional[int] = None
    grade: str = "10"
    school: Optional[str] = None
    language_preference: str = "both"


class DiagnosticRequest(BaseModel):
    subject: str
    chapter: str
    concepts: List[str]
    difficulty: str = "mixed"
    questions_per_concept: int = 3


class EvaluateTestRequest(BaseModel):
    student_id: int
    subject: str
    chapter: str
    questions: List[Dict]
    answers: Dict[str, str]


class LearningPathRequest(BaseModel):
    student_id: int
    subject: str
    chapter: str
    mastery_scores: Dict[str, float]


class TutorRequest(BaseModel):
    mode: str = "concept"            # "concept" | "question"
    subject: str
    chapter: str = ""
    concept: Optional[str] = None
    question: Optional[str] = None
    language: str = "both"


class QuizRequest(BaseModel):
    subject: str
    chapter: str
    concept: str
    difficulty: str = "medium"
    num_questions: int = 5


class MasteryUpdateRequest(BaseModel):
    student_id: int
    concept: str
    subject: str
    chapter: str = ""
    quiz_score: float
    time_spent: int = 0


# ── Small helpers ─────────────────────────────────────────────────────────────
def _validate_student(student_id: int, db: Session) -> Student:
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


def _get_llm_client_safe():
    """Return an LLM client, or None if EduSakhi LLM deps/token unavailable."""
    try:
        from llm.tutor import get_llm_client
        if not settings.HF_API_TOKEN:
            return None
        return get_llm_client()
    except Exception as e:
        logger.warning(f"LLM client unavailable: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# Knowledge base (automated PDF ingestion)
# ══════════════════════════════════════════════════════════════════════════════
@app.post("/upload-pdf", tags=["Knowledge Base"])
async def upload_pdf(file: UploadFile = File(...), subject: str = Form(...)):
    """Upload an NCERT PDF → automatically ingested into the knowledge base."""
    from rag.ingest import ingest_pdf

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    dest = os.path.join(settings.UPLOAD_DIR, file.filename)
    with open(dest, "wb") as f:
        f.write(await file.read())

    result = ingest_pdf(dest, subject)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Ingestion failed"))
    return result


@app.get("/knowledge-base/stats", tags=["Knowledge Base"])
def knowledge_base_stats():
    from rag.ingest import get_ingestion_stats
    return get_ingestion_stats()


# ══════════════════════════════════════════════════════════════════════════════
# Students
# ══════════════════════════════════════════════════════════════════════════════
@app.post("/students", tags=["Students"])
def create_student(data: StudentCreate, db: Session = Depends(get_db)):
    student = Student(**data.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return {"id": student.id, "name": student.name, "grade": student.grade}


@app.get("/students/{student_id}", tags=["Students"])
def get_student(student_id: int, db: Session = Depends(get_db)):
    s = _validate_student(student_id, db)
    return {
        "id": s.id, "name": s.name, "age": s.age, "grade": s.grade,
        "school": s.school, "language_preference": s.language_preference,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Diagnostics
# ══════════════════════════════════════════════════════════════════════════════
@app.post("/generate-diagnostic-test", tags=["Diagnostics"])
def generate_diagnostic_test(req: DiagnosticRequest):
    from adaptive_engine.diagnostic import DiagnosticEngine
    engine = DiagnosticEngine()
    return engine.generate_diagnostic_test(
        subject=req.subject,
        chapter=req.chapter,
        concepts=req.concepts,
        difficulty=req.difficulty,
        questions_per_concept=req.questions_per_concept,
        llm_client=_get_llm_client_safe(),
        model=settings.HF_MODEL,
    )


@app.post("/evaluate-test", tags=["Diagnostics"])
def evaluate_test(req: EvaluateTestRequest, db: Session = Depends(get_db)):
    from adaptive_engine.diagnostic import DiagnosticEngine
    from analytics.performance import PerformanceAnalytics

    _validate_student(req.student_id, db)
    engine = DiagnosticEngine()
    result = engine.evaluate_test(req.answers, req.questions)

    # Persist mastery from the diagnostic.
    analytics = PerformanceAnalytics()
    for concept, score in result["mastery_scores"].items():
        analytics.upsert_concept_mastery(
            student_id=req.student_id, concept=concept, subject=req.subject,
            chapter=req.chapter, new_mastery=score, quiz_score=score,
            time_spent=0, db=db,
        )
    return result


# ══════════════════════════════════════════════════════════════════════════════
# Adaptive learning path
# ══════════════════════════════════════════════════════════════════════════════
@app.post("/generate-learning-path", tags=["Adaptive Learning"])
def generate_learning_path(req: LearningPathRequest, db: Session = Depends(get_db)):
    from adaptive_engine.recommendation import RecommendationEngine
    from database.models import LearningPath

    _validate_student(req.student_id, db)
    engine = RecommendationEngine()
    path = engine.generate_learning_path(req.mastery_scores, req.subject, req.chapter)

    db.add(LearningPath(
        student_id=req.student_id, subject=req.subject,
        chapter=req.chapter, path_data=path,
    ))
    db.commit()
    return path


# ══════════════════════════════════════════════════════════════════════════════
# AI Tutor
# ══════════════════════════════════════════════════════════════════════════════
@app.post("/ask-tutor", tags=["AI Tutor"])
def ask_tutor(req: TutorRequest):
    from llm.tutor import AITutor
    tutor = AITutor()
    if req.mode == "question":
        if not req.question:
            raise HTTPException(status_code=400, detail="`question` is required in question mode.")
        return tutor.answer_question(req.question, req.subject, req.chapter)
    if not req.concept:
        raise HTTPException(status_code=400, detail="`concept` is required in concept mode.")
    return tutor.explain_concept(req.concept, req.subject, req.chapter, req.language)


# ══════════════════════════════════════════════════════════════════════════════
# Quizzes
# ══════════════════════════════════════════════════════════════════════════════
@app.post("/generate-quiz", tags=["Quizzes"])
def generate_quiz(req: QuizRequest):
    from llm.quiz_generator import QuizGenerator
    gen = QuizGenerator()
    return gen.generate_quiz(
        subject=req.subject, chapter=req.chapter, concept=req.concept,
        difficulty=req.difficulty, num_questions=req.num_questions,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Mastery update
# ══════════════════════════════════════════════════════════════════════════════
@app.post("/update-mastery", tags=["Mastery"])
def update_mastery(req: MasteryUpdateRequest, db: Session = Depends(get_db)):
    from adaptive_engine.mastery import MasteryEngine
    from analytics.performance import PerformanceAnalytics
    from database.models import ConceptMastery

    _validate_student(req.student_id, db)
    engine = MasteryEngine()

    existing = (
        db.query(ConceptMastery)
        .filter(
            ConceptMastery.student_id == req.student_id,
            ConceptMastery.concept == req.concept,
            ConceptMastery.subject == req.subject,
        )
        .first()
    )
    old = existing.mastery_score if existing else 0.0
    new = engine.update_mastery(old, req.quiz_score)

    analytics = PerformanceAnalytics()
    improvement = analytics.upsert_concept_mastery(
        student_id=req.student_id, concept=req.concept, subject=req.subject,
        chapter=req.chapter, new_mastery=new, quiz_score=req.quiz_score,
        time_spent=req.time_spent, db=db,
    )
    return improvement


# ══════════════════════════════════════════════════════════════════════════════
# Profile & analytics
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/student-profile/{student_id}", tags=["Analytics"])
def student_profile(student_id: int, db: Session = Depends(get_db)):
    from analytics.performance import PerformanceAnalytics
    return PerformanceAnalytics().get_student_profile(student_id, db)


@app.get("/learning-analytics/{student_id}", tags=["Analytics"])
def learning_analytics(student_id: int, db: Session = Depends(get_db)):
    from analytics.performance import PerformanceAnalytics
    return PerformanceAnalytics().get_learning_analytics(student_id, db)


# ══════════════════════════════════════════════════════════════════════════════
# Concept graph
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/concept-graph", tags=["Concept Graph"])
def concept_graph(concepts: Optional[str] = None):
    from adaptive_engine.dependency_graph import ConceptDependencyGraph
    graph = ConceptDependencyGraph()
    filter_list = [c.strip() for c in concepts.split(",")] if concepts else None
    return graph.get_graph_data(filter_list)


@app.get("/concept-prerequisites/{concept}", tags=["Concept Graph"])
def concept_prerequisites(concept: str):
    from adaptive_engine.dependency_graph import ConceptDependencyGraph
    graph = ConceptDependencyGraph()
    return {
        "concept": concept,
        "prerequisites": graph.get_prerequisites(concept),
        "next_concepts": graph.get_next_concepts(concept),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Health
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "app": settings.APP_NAME, "llm_configured": bool(settings.HF_API_TOKEN)}
