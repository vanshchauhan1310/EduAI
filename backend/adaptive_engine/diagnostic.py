"""
Diagnostic Assessment Engine
============================
Generates a chapter-wise diagnostic test (Easy/Medium/Hard MCQs) using the LLM,
then evaluates the student's answers to produce per-concept mastery scores.

If no LLM token is configured, falls back to placeholder questions so the
system still runs end-to-end.
"""

import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DiagnosticEngine:
    """Creates and grades diagnostic tests."""

    # ── Test generation ───────────────────────────────────────────────────────
    def generate_diagnostic_test(
        self,
        subject:               str,
        chapter:               str,
        concepts:              List[str],
        difficulty:            str = "mixed",
        questions_per_concept: int = 3,
        llm_client=None,
        model:                 str = "Qwen/Qwen3-8B",
    ) -> Dict:
        """
        Generate a diagnostic test covering the given concepts.

        Returns a dict with the full question list (each question carries the
        concept it belongs to, so we can score per concept later).
        """
        questions: List[Dict] = []

        for concept in concepts:
            concept_qs = self._generate_for_concept(
                subject, chapter, concept, difficulty,
                questions_per_concept, llm_client, model,
            )
            questions.extend(concept_qs)

        # Number questions globally
        for i, q in enumerate(questions, 1):
            q["question_no"] = i

        return {
            "subject":         subject,
            "chapter":         chapter,
            "concepts":        concepts,
            "difficulty":      difficulty,
            "total_questions": len(questions),
            "questions":       questions,
        }

    def _generate_for_concept(
        self, subject, chapter, concept, difficulty,
        count, llm_client, model,
    ) -> List[Dict]:
        if llm_client is None:
            return self._placeholder_questions(concept, count)

        prompt = f"""You are a CBSE Class 10 examiner.
Generate exactly {count} multiple-choice questions to test a student's
understanding of the concept "{concept}" from {subject} chapter "{chapter}".
Difficulty: {difficulty.upper()}.

Format EACH question EXACTLY like this:

Q[n]. [Question text]
A) [option]
B) [option]
C) [option]
D) [option]
ANSWER: [correct letter]
EXPLANATION: [one short sentence]

Generate all {count} questions now:"""

        try:
            response = llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are a CBSE Class 10 examiner. Follow the format exactly."},
                    {"role": "user",   "content": prompt},
                ],
                max_tokens=900,
                temperature=0.7,
            )
            raw = response.choices[0].message.content
            parsed = self._parse_questions(raw, concept)
            return parsed if parsed else self._placeholder_questions(concept, count)
        except Exception as e:
            logger.error(f"Diagnostic generation failed for {concept}: {e}")
            return self._placeholder_questions(concept, count)

    # ── Parsing ───────────────────────────────────────────────────────────────
    def _parse_questions(self, raw: str, concept: str) -> List[Dict]:
        questions = []
        parts = re.split(r"(?=Q\d+\.)", raw)

        for part in parts:
            part = part.strip()
            if not part or not re.match(r"Q\d+\.", part):
                continue

            lines = [l.strip() for l in part.split("\n") if l.strip()]
            m = re.match(r"Q\d+\.\s*(.*)", lines[0])
            if not m:
                continue

            q = {
                "concept":     concept,
                "question":    m.group(1).strip(),
                "options":     [],
                "answer":      "",
                "explanation": "",
            }
            for line in lines[1:]:
                if re.match(r"^[A-D]\)", line):
                    q["options"].append(line)
                elif line.upper().startswith("ANSWER:"):
                    q["answer"] = line.split(":", 1)[-1].strip()
                elif line.upper().startswith("EXPLANATION:"):
                    q["explanation"] = line.split(":", 1)[-1].strip()

            if q["question"]:
                questions.append(q)

        return questions

    def _placeholder_questions(self, concept: str, count: int) -> List[Dict]:
        return [
            {
                "concept":     concept,
                "question":    f"[Sample] Which statement best describes {concept}?",
                "options":     ["A) Option A", "B) Option B", "C) Option C", "D) Option D"],
                "answer":      "A",
                "explanation": "Placeholder question — set HF_API_TOKEN and upload NCERT PDFs for real questions.",
            }
            for _ in range(count)
        ]

    # ── Evaluation ────────────────────────────────────────────────────────────
    def evaluate_test(
        self,
        student_answers: Dict[str, str],   # {"1": "B", "2": "A", ...}
        questions:       List[Dict],
    ) -> Dict:
        """
        Grade answers and compute mastery score per concept.
        mastery_score(concept) = correct_in_concept / total_in_concept
        """
        per_concept: Dict[str, Dict[str, int]] = {}
        correct_total = 0

        for q in questions:
            q_no        = str(q.get("question_no", ""))
            concept     = q.get("concept", "unknown")
            correct_ans = q.get("answer", "").strip().upper()[:1]
            student_ans = student_answers.get(q_no, "").strip().upper()[:1]

            per_concept.setdefault(concept, {"correct": 0, "total": 0})
            per_concept[concept]["total"] += 1

            if student_ans and student_ans == correct_ans:
                per_concept[concept]["correct"] += 1
                correct_total += 1

        concept_scores = {
            c: {"correct": d["correct"], "total": d["total"]}
            for c, d in per_concept.items()
        }
        mastery_scores = {
            c: round(d["correct"] / d["total"], 4) if d["total"] else 0.0
            for c, d in per_concept.items()
        }

        total = len(questions)
        return {
            "concept_scores":     concept_scores,
            "mastery_scores":     mastery_scores,
            "total_questions":    total,
            "correct_answers":    correct_total,
            "overall_percentage": round(correct_total / total * 100, 2) if total else 0.0,
        }
