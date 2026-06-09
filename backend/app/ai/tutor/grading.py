# app/ai/tutor/grading.py
"""
Pure scoring/progression functions (ported 1:1 from prototype/learning_system.py).

Operate on plain dicts (the mobile posts the generated `quiz` array back as JSON for
the stateless grading endpoint — see aiTutorService.ts `gradeQuiz`), not Pydantic
QuizItem models, since there's no LangChain layer here.

Quiz item shape expected: {question, type, difficulty, concept_tested, options,
answer, explanation}. Answers are keyed by the quiz item's index (string or int).
"""

import re
from typing import Dict, List

from app.ai.tutor import curriculum

# A learner must score at least this (%) to advance to the next concept.
PASS_THRESHOLD = 70.0

_LETTER_RE = re.compile(r"[A-Da-d]")


def quiz_distribution(mastery: float, total: int = 10) -> Dict[str, int]:
    """Adaptive Easy/Medium/Hard question counts, scaled to `total` (the
    student-chosen quiz length). Easy-heavy for beginners, hard-heavy for advanced."""
    if mastery < 40:
        ratio = {"Easy": 0.7, "Medium": 0.3, "Hard": 0.0}
    elif mastery <= 70:
        ratio = {"Easy": 0.4, "Medium": 0.4, "Hard": 0.2}
    else:
        ratio = {"Easy": 0.2, "Medium": 0.4, "Hard": 0.4}

    counts = {k: int(total * r) for k, r in ratio.items()}
    remainder = total - sum(counts.values())
    if remainder > 0:
        dominant = max(ratio, key=ratio.get)
        counts[dominant] += remainder
    return counts


def update_mastery(old: float, quiz_pct: float) -> float:
    """EMA on the 0-100 scale: new = 0.6*old + 0.4*quiz_pct."""
    new = 0.6 * old + 0.4 * quiz_pct
    return round(min(100.0, max(0.0, new)), 1)


def _letters(s: str) -> set:
    """Set of option letters (A-D) found in a string, e.g. 'A,C' -> {'A','C'}."""
    return {c.upper() for c in _LETTER_RE.findall(s or "")}


def _classify_type(item: Dict) -> str:
    """Decide a question's REAL type from its structure, not its label:
    options present -> MCQ (1 correct) / MSQ (2+ correct); no options -> Short/Long."""
    if item.get("options"):
        return "MSQ" if len(_letters(item.get("answer", ""))) > 1 else "MCQ"
    label = (item.get("type") or "").strip().lower()
    return "Long Answer" if "long" in label else "Short Answer"


def grade(quiz: List[Dict], answers: Dict) -> Dict:
    """Auto-grades MCQ + MSQ; Short/Long answers are returned ungraded
    (is_correct=None) for the student's self-review — matches the mobile
    `QuizGradeResult` shape (`is_correct: boolean | null`)."""
    graded, scored, correct = [], 0, 0
    for i, item in enumerate(quiz):
        item_type = (item.get("type") or _classify_type(item)).upper()
        given_raw = str(answers.get(i, answers.get(str(i), "")) or "")
        ok = None
        correct_answer = item.get("answer", "")
        if item_type == "MCQ" and item.get("options"):
            scored += 1
            ok = _letters(given_raw) == _letters(correct_answer) and len(_letters(correct_answer)) == 1
            correct += int(ok)
        elif item_type == "MSQ" and item.get("options"):
            scored += 1
            ok = (_letters(given_raw) == _letters(correct_answer)) and bool(_letters(correct_answer))
            correct += int(ok)
        graded.append({
            "index": i,
            "question": item.get("question", ""),
            "type": item.get("type", item_type),
            "difficulty": item.get("difficulty", ""),
            "concept": item.get("concept_tested", ""),
            "given": given_raw,
            "correct_answer": correct_answer,
            "is_correct": ok,
            "explanation": item.get("explanation", ""),
        })
    pct = round(correct / scored * 100, 1) if scored else 0.0
    return {"correct": correct, "scored": scored, "percentage": pct, "results": graded}


def progress_decision(graded: Dict, subject: str, chapter: str, concept: str) -> Dict:
    """score >= PASS_THRESHOLD -> advance to the next concept in the module.
    score <  PASS_THRESHOLD -> re-attempt; recommend reviewing the concepts tied
    to the missed questions + the concept's last two prerequisites."""
    pct = graded["percentage"]
    passed = pct >= PASS_THRESHOLD

    if passed:
        nxt = curriculum.next_concept(subject, chapter, concept)
        return {
            "passed": True, "percentage": pct, "threshold": PASS_THRESHOLD,
            "action": "advance",
            "next_concept": nxt,
            "review_topics": [],
            "message": (f"Passed with {pct:.0f}% (≥ {PASS_THRESHOLD:.0f}%). "
                        + (f"Advancing to the next concept: {nxt}."
                           if nxt else "You've finished this chapter's concepts!")),
        }

    missed = [r["concept"] for r in graded["results"]
              if r["is_correct"] is False and r["concept"]]
    review = list(dict.fromkeys(missed)) or [concept]
    prereqs = curriculum.prerequisites(subject, chapter, concept)
    if prereqs:
        review = list(dict.fromkeys(review + prereqs[-2:]))
    return {
        "passed": False, "percentage": pct, "threshold": PASS_THRESHOLD,
        "action": "reattempt",
        "next_concept": None,
        "review_topics": review,
        "message": (f"Scored {pct:.0f}% (need ≥ {PASS_THRESHOLD:.0f}% to advance). "
                    "Review the topics below and re-attempt the quiz."),
    }
