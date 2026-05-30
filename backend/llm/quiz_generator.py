"""
Adaptive Quiz Generator
========================
Generates MCQ and short-answer quizzes using the LLM + RAG pipeline.
Difficulty adapts to the student's current mastery level.

Quiz types
----------
MCQ          – 4-option multiple choice
SHORT_ANSWER – 1-2 sentence written answer
"""

import re
import os
import logging
from typing import Dict, List

from dotenv import load_dotenv

from rag.retriever import RAGRetriever
from llm.tutor import get_llm_client

load_dotenv()
logger = logging.getLogger(__name__)

HF_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen3-8B")


class QuizGenerator:
    """
    Generates context-aware adaptive quizzes from NCERT content.
    """

    def __init__(self):
        self.retriever = RAGRetriever(top_k=5)

    # ── Quiz generation ───────────────────────────────────────────────────────
    def generate_quiz(
        self,
        subject:       str,
        chapter:       str,
        concept:       str,
        difficulty:    str = "medium",    # easy | medium | hard
        num_questions: int = 5,
    ) -> Dict:
        """
        Generate an adaptive quiz grounded in NCERT textbook content.

        Parameters
        ----------
        subject       : "Physics"
        chapter       : "Electricity"
        concept       : "Ohms Law"
        difficulty    : "easy" | "medium" | "hard"
        num_questions : number of questions to generate
        """
        # ── RAG retrieval ─────────────────────────────────────────────────────
        context = self.retriever.get_context(
            f"{concept} {chapter} {subject}",
            subject=subject,
            top_k=5,
        )
        sources = self.retriever.get_sources(
            concept, subject=subject, top_k=3
        )

        context_block = (
            f"\n\nRelevant NCERT content:\n{context}\n"
            if context else ""
        )

        # ── LLM prompt ────────────────────────────────────────────────────────
        prompt = f"""You are an expert CBSE Class 10 exam creator.

Generate exactly {num_questions} questions for:
Subject: {subject}
Chapter: {chapter}
Topic: {concept}
Difficulty: {difficulty.upper()}
{context_block}

Difficulty guidelines:
- EASY: Basic recall, definitions, fill-in-the-blanks style
- MEDIUM: Application, formula-based, concept explanation
- HARD: Multi-step problems, analysis, "why" questions

Mix of question types: mostly MCQ, 1-2 short answer.

Format EACH question EXACTLY like this:

Q[n]. [Question text]
TYPE: MCQ
A) [option]
B) [option]
C) [option]
D) [option]
ANSWER: [correct letter]
EXPLANATION: [one sentence]

For short answer:
Q[n]. [Question text]
TYPE: SHORT_ANSWER
ANSWER: [expected answer in 1-2 sentences]
EXPLANATION: [why this is the answer]

Generate all {num_questions} questions now:"""

        questions: List[Dict] = []

        try:
            client   = get_llm_client()
            response = client.chat_completion(
                messages=[
                    {
                        "role":    "system",
                        "content": "You are an expert CBSE Class 10 question paper creator. Follow the format exactly.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1400,
                temperature=0.75,
            )
            raw       = response.choices[0].message.content
            questions = self._parse_quiz(raw)

        except Exception as e:
            logger.error(f"Quiz generation failed for {concept}: {e}")
            questions = self._fallback_questions(concept, difficulty, num_questions)

        return {
            "subject":         subject,
            "chapter":         chapter,
            "concept":         concept,
            "difficulty":      difficulty,
            "total_questions": len(questions),
            "questions":       questions,
            "sources":         sources,
        }

    # ── Quiz evaluation ───────────────────────────────────────────────────────
    def evaluate_quiz(
        self,
        student_answers: Dict[str, str],   # {"1": "B", "2": "A", ...}
        questions:       List[Dict],
    ) -> Dict:
        """
        Score a submitted quiz and return per-question results.

        For MCQ: exact letter match.
        For SHORT_ANSWER: score 1 if answer length > 15 chars (presence check).
        """
        correct = 0
        results = []

        for q in questions:
            q_no        = str(q["question_no"])
            student_ans = student_answers.get(q_no, "").strip()
            correct_ans = q.get("answer", "").strip()
            q_type      = q.get("type", "MCQ")

            is_correct = False
            if q_type == "MCQ":
                is_correct = (
                    student_ans.upper()[:1] == correct_ans.upper()[:1]
                ) if student_ans and correct_ans else False
            elif q_type == "SHORT_ANSWER":
                is_correct = len(student_ans) > 15

            if is_correct:
                correct += 1

            results.append({
                "question_no":    q["question_no"],
                "question":       q.get("question", ""),
                "correct":        is_correct,
                "student_answer": student_ans,
                "correct_answer": correct_ans,
                "explanation":    q.get("explanation", ""),
            })

        total      = len(questions)
        score      = round(correct / total, 4) if total else 0.0
        percentage = round(score * 100, 2)

        return {
            "total":      total,
            "correct":    correct,
            "score":      score,
            "percentage": percentage,
            "results":    results,
        }

    # ── Parsing helpers ───────────────────────────────────────────────────────
    def _parse_quiz(self, raw: str) -> List[Dict]:
        """Parse LLM output into structured question dicts."""
        questions = []

        # Split on Q1. Q2. Q3. markers
        parts = re.split(r"(?=Q\d+\.)", raw)

        for part in parts:
            part = part.strip()
            if not part or not re.match(r"Q\d+\.", part):
                continue

            lines = [l.strip() for l in part.split("\n") if l.strip()]
            if len(lines) < 3:
                continue

            # Extract question number and text
            first_line = lines[0]
            m = re.match(r"Q(\d+)\.\s*(.*)", first_line)
            if not m:
                continue

            q_no   = int(m.group(1))
            q_text = m.group(2).strip()

            q: Dict = {
                "question_no": q_no,
                "question":    q_text,
                "type":        "MCQ",
                "options":     [],
                "answer":      "",
                "explanation": "",
            }

            for line in lines[1:]:
                if line.upper().startswith("TYPE:"):
                    q["type"] = line.split(":", 1)[-1].strip().upper()
                elif re.match(r"^[A-D]\)", line):
                    q["options"].append(line)
                elif line.upper().startswith("ANSWER:"):
                    q["answer"] = line.split(":", 1)[-1].strip()
                elif line.upper().startswith("EXPLANATION:"):
                    q["explanation"] = line.split(":", 1)[-1].strip()

            if q["question"]:
                questions.append(q)

        return questions

    def _fallback_questions(
        self, concept: str, difficulty: str, count: int
    ) -> List[Dict]:
        return [
            {
                "question_no": i + 1,
                "question":    f"Define {concept} and give an example.",
                "type":        "SHORT_ANSWER",
                "options":     [],
                "answer":      f"Please refer to your NCERT textbook for the definition of {concept}.",
                "explanation": "No LLM available. Upload NCERT PDFs and set HF_API_TOKEN.",
            }
            for i in range(count)
        ]
