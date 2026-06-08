"""
Board-style exam paper generator (RAG-grounded)
================================================
Produces subjective CBSE-style questions in the SAME schema as the teammate's
exam_prep module (question_text, sample_answer, expected_points, marks), so the
output is directly consumable by their AssessmentGenerator / grading.

Grounded in the Class 10 knowledge base + ingested PDFs via rag.grounding().
"""

import uuid
from typing import List, Optional

from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

from schemas import ExamQuestion, Assessment
import rag
import curriculum
from learning_system import _parse_model   # reuse the json-repair tolerant parser
from llm_provider import get_chat_model


class _ExamList(BaseModel):
    questions: List[ExamQuestion] = []


# Marks pattern (mirrors a simple pattern_library): difficulty -> typical marks.
_MARKS = {"Easy": 1, "Medium": 3, "Hard": 5}


_EXAM_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are an expert CBSE Class 10 board examiner. Generate NEW subjective "
     "questions that test conceptual understanding. Return ONLY valid JSON. "
     "expected_points MUST be a list of short strings."),
    ("human",
     "Subject: {subject}\nChapter: {chapter}\nConcept: {concept}\n"
     "Difficulty: {difficulty}.\n"
     "Base the questions on this textbook content as the PRIMARY source "
     "(prefer its facts, examples and numbers):\n{rag}\n\n"
     "Generate exactly {n} questions. Use a mix of marks (1, 2, 3 or 5). "
     "For Physics/Mathematics include at least one Numerical.\n"
     "RULES: 'expected_points' must be 2-4 SHORT STRINGS describing what a correct "
     "answer must contain (the marking scheme) — NOT numbers, NOT the marks. "
     "'sample_answer' must directly and fully answer the question.\n"
     "Example item: {{\"question_text\": \"State Ohm's Law and its formula.\", "
     "\"type\": \"Subjective\", \"difficulty\": \"Easy\", \"marks\": 2, "
     "\"concept_tested\": \"Ohm's Law\", \"sample_answer\": \"Ohm's Law states the "
     "current is directly proportional to the voltage at constant temperature; V = IR.\", "
     "\"expected_points\": [\"Current proportional to voltage\", \"Condition: constant "
     "temperature\", \"Formula V = IR with symbols\"]}}\n"
     'Return JSON {{"questions": [ {{ "question_text": "", "type": '
     '"Subjective|Numerical", "difficulty": "Easy|Medium|Hard", "marks": 3, '
     '"concept_tested": "", "sample_answer": "", "expected_points": ["", ""] }} ] }}'),
])


class ExamGenerator:
    def __init__(self):
        model = get_chat_model()
        self.chain = _EXAM_PROMPT | model | StrOutputParser() | _parse_model(_ExamList)

    def generate_assessment(
        self,
        subject: str,
        chapter: str,
        concept: str,
        difficulty: str = "Medium",
        num_questions: int = 5,
        rag_content: Optional[str] = None,
    ) -> Assessment:
        prereqs = curriculum.prerequisites(subject, chapter, concept)
        if rag_content is None:
            rag_content, _ = rag.grounding(subject, chapter, concept,
                                           extra_terms=" ".join(prereqs[-2:]), k=5)
        rag_text = (rag_content or "").strip() or "(use standard CBSE Class 10 knowledge)"

        try:
            parsed: _ExamList = self.chain.invoke({
                "subject": subject, "chapter": chapter, "concept": concept,
                "difficulty": difficulty, "n": num_questions, "rag": rag_text,
            })
            questions = parsed.questions
        except Exception:
            questions = []

        # Fill any missing marks from the difficulty pattern.
        for q in questions:
            if not q.marks or q.marks <= 0:
                q.marks = _MARKS.get(q.difficulty, 3)

        return Assessment(
            assessment_id=str(uuid.uuid4()),
            chapter_id=f"{subject}:{chapter}",
            difficulty=difficulty,
            total_questions=len(questions),
            total_marks=sum(q.marks for q in questions),
            questions=questions,
        )
