"""
Adaptive Tutor Engine (LangChain)
=================================
Implements the tutor spec for CBSE Class 10 PCM, English + Telugu medium.

Inputs : subject, chapter, concept, mastery (0-100), optional RAG/NCERT content,
         optional prior quiz responses.
Output : a structured TutorResponse (student analysis, learning path, bilingual
         lesson, adaptive quiz, mastery recommendation).

Reliability: a 7B model struggles to emit one huge bilingual JSON, so we make
three focused LangChain calls and assemble the result:
    1. CORE   -> analysis + learning_path + lesson(English) + recommendations
    2. QUIZ   -> adaptive quiz (counts depend on mastery band)
    3. TELUGU -> translate the English explanation into Telugu
"""

import re
from typing import Dict, List, Optional

import json_repair
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from langchain_core.runnables import RunnableLambda

from schemas import (
    TutorResponse, StudentAnalysis, LearningPathItem, Lesson, QuizItem,
    Recommendations,
)
from llm_provider import get_chat_model, using_real_llm
import rag
import curriculum


LANGUAGES = {"english": "English", "telugu": "తెలుగు (Telugu)", "both": "English + Telugu"}

# A learner must score at least this (%) to advance to the next concept.
PASS_THRESHOLD = 70.0


# ── Mastery bands (0-100) ─────────────────────────────────────────────────────
def level_for(mastery: float) -> str:
    if mastery <= 40:
        return "Beginner"
    if mastery <= 70:
        return "Intermediate"
    return "Advanced"


def quiz_distribution(mastery: float, total: int = 10) -> Dict[str, int]:
    """Adaptive question counts, scaled to a student-chosen total.

    The proportions follow the spec (easy-heavy for beginners, hard-heavy for
    advanced); `total` lets the student pick how many questions to attempt.
    """
    if mastery < 40:
        ratio = {"Easy": 0.7, "Medium": 0.3, "Hard": 0.0}
    elif mastery <= 70:
        ratio = {"Easy": 0.4, "Medium": 0.4, "Hard": 0.2}
    else:
        ratio = {"Easy": 0.2, "Medium": 0.4, "Hard": 0.4}

    counts = {k: int(total * r) for k, r in ratio.items()}
    # Give any rounding remainder to the dominant band.
    remainder = total - sum(counts.values())
    if remainder > 0:
        dominant = max(ratio, key=ratio.get)
        counts[dominant] += remainder
    return counts


def update_mastery(old: float, quiz_pct: float) -> float:
    """EMA on the 0-100 scale."""
    new = 0.6 * old + 0.4 * quiz_pct
    return round(min(100.0, max(0.0, new)), 1)


# ── Internal parse models ─────────────────────────────────────────────────────
class _CorePlan(BaseModel):
    student_analysis: StudentAnalysis
    learning_path: List[LearningPathItem] = []
    lesson: Lesson
    recommendations: Recommendations


class _QuizList(BaseModel):
    quiz: List[QuizItem] = []


def _extract_json(text: str) -> str:
    t = text.strip()
    if "```" in t:
        for p in t.split("```"):
            p = p.lstrip("json").strip()
            if p.startswith("{"):
                t = p
                break
    start, end = t.find("{"), t.rfind("}")
    return t[start:end + 1] if start != -1 and end > start else t


def _parse_model(model_cls):
    """Tolerant parser: repair the LLM JSON (handles raw newlines in strings,
    trailing commas, fences) then validate against the Pydantic model."""
    def _fn(text: str):
        data = json_repair.loads(_extract_json(text))
        return model_cls.model_validate(data)
    return RunnableLambda(_fn)


# ── Prompts ────────────────────────────────────────────────────────────────────
_CORE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are an AI-Powered Personalized Adaptive Learning Tutor for CBSE Class 10 "
     "Government School students (Physics, Chemistry, Mathematics), English & Telugu "
     "medium. You act as teacher, assessment expert and adaptive learning engine. "
     "Use the provided NCERT content as the primary source; do NOT hallucinate. "
     "Keep explanations age-appropriate for Class 10. Return ONLY valid JSON."),
    ("human",
     "Subject: {subject}\nChapter: {chapter}\nConcept: {concept}\n"
     "Student Mastery Score (0-100): {mastery}\nLearning level: {level}\n"
     "Prior quiz responses: {quiz_responses}\n"
     "Retrieved NCERT content:\n{rag}\n\n"
     "Produce a JSON object with EXACTLY these keys: student_analysis, learning_path, "
     "lesson, recommendations (DO NOT include a quiz here).\n"
     "- student_analysis: level, strong_concepts, weak_concepts, misconceptions.\n"
     "- learning_path: ordered list (weakest concept first, respect prerequisites) "
     "with concept, priority, reason, estimated_time, activity.\n"
     "- lesson: concept, english_explanation (clear, with CBSE terminology), "
     "real_life_examples, worked_examples (numerical for Physics/Maths), "
     "common_mistakes, revision_notes. SET telugu_explanation to \"\" (added later).\n"
     "- recommendations: next_concepts, estimated_mastery_score, next_lesson.\n"
     "{format_instructions}"),
])

_QUIZ_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are an expert CBSE Class 10 examiner. Generate an adaptive quiz that tests "
     "conceptual understanding (not rote). Return ONLY valid JSON. Write in English."),
    ("human",
     "Subject: {subject}\nChapter: {chapter}\nConcept: {concept}\n"
     "Prerequisite concepts: {prereqs}\n"
     "Mastery: {mastery} ({level}).\n"
     "Base the questions on the following NCERT / textbook content as the PRIMARY "
     "source — prefer facts, examples and numbers found here over general knowledge. "
     "At least half the questions MUST be answerable directly from this content:\n"
     "{rag}\n\n"
     "Generate EXACTLY {n} questions with this difficulty mix: {dist}. "
     "EVERY question MUST be one of these types ONLY: {types}. Do NOT produce any "
     "other type — no Short/Long answer unless it is listed. Spread evenly across "
     "the listed types. If MCQ or MSQ is listed, those questions MUST include 4 "
     "options 'A) '..'D) '.\n"
     "Type rules:\n"
     "- MCQ: exactly 4 options 'A) '..'D) ', exactly ONE correct; answer = one letter.\n"
     "- MSQ: exactly 4 options 'A) '..'D) ', TWO OR MORE correct; answer = the correct "
     "letters comma-separated, e.g. 'A,C'.\n"
     "- Short Answer: options = []; answer = the expected answer in 1-2 sentences.\n"
     "- Long Answer: options = []; answer = a model answer in 3-5 sentences.\n"
     "Return JSON {{\"quiz\": [ ... ]}} where each item has: question, type "
     "(one of {types}), difficulty (Easy|Medium|Hard), concept_tested, options, "
     "answer, explanation.\n"
     "{format_instructions}"),
])

_TRANSLATE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a precise English-to-Telugu translator for CBSE Class 10 science/maths. "
     "Translate the text into simple, correct Telugu (తెలుగు) suitable for a 15-year-old. "
     "Output ONLY the Telugu translation."),
    ("human", "{text}"),
])

_TRANSLATE_LINES_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a precise English-to-Telugu translator for CBSE Class 10 science/maths. "
     "Each segment is prefixed with a marker like <<1>>. Translate ONLY the text after "
     "each marker into simple Telugu (తెలుగు). Reproduce every marker EXACTLY, each "
     "followed by its Telugu translation. Keep numbers and math symbols (V=IR, ohms) as is. "
     "Output nothing except the markers and their translations."),
    ("human", "{lines}"),
])

_MARK_RE = re.compile(r"<<(\d+)>>\s*(.*?)(?=(?:<<\d+>>)|\Z)", re.S)

_OPT_RE = re.compile(r"^\s*([A-Da-d])\)\s*(.*)$", re.S)


def _split_option(opt: str):
    m = _OPT_RE.match(opt)
    if m:
        return m.group(1).upper(), m.group(2).strip()
    return "", opt.strip()


def _letters(s: str) -> set:
    """Set of option letters (A-D) found in a string, e.g. 'A,C' -> {'A','C'}."""
    return {c.upper() for c in re.findall(r"[A-Da-d]", s or "")}


def _classify_type(q) -> str:
    """Decide a question's REAL type from its structure, not the model's label:
    options present -> MCQ (1 correct) / MSQ (2+ correct); no options -> Short/Long."""
    if q.options:
        return "MSQ" if len(_letters(q.answer)) > 1 else "MCQ"
    label = (q.type or "").strip().lower()
    return "Long Answer" if "long" in label else "Short Answer"


class AdaptiveTutor:
    def __init__(self):
        self.using_llm = using_real_llm()
        model = get_chat_model()
        _clean = RunnableLambda(_extract_json)

        self._core_parser = PydanticOutputParser(pydantic_object=_CorePlan)
        self._quiz_parser = PydanticOutputParser(pydantic_object=_QuizList)

        self.core_chain = (
            _CORE_PROMPT.partial(format_instructions=self._core_parser.get_format_instructions())
            | model | StrOutputParser() | _parse_model(_CorePlan)
        )
        self.quiz_chain = (
            _QUIZ_PROMPT.partial(format_instructions=self._quiz_parser.get_format_instructions())
            | model | StrOutputParser() | _parse_model(_QuizList)
        )
        self.translate_chain = _TRANSLATE_PROMPT | model | StrOutputParser()
        self.translate_lines_chain = _TRANSLATE_LINES_PROMPT | model | StrOutputParser()

    # ── Main entry point ───────────────────────────────────────────────────────
    def generate(
        self,
        subject: str,
        chapter: str,
        concept: str,
        mastery: float,
        language: str = "both",
        rag_content: str = "",
        quiz_responses: Optional[str] = None,
        with_quiz: bool = True,
        num_questions: int = 10,
        q_types: Optional[List[str]] = None,
    ) -> TutorResponse:
        level = level_for(mastery)
        # RAG: pull grounding notes from the Class 10 knowledge base if none supplied.
        if not rag_content.strip():
            rag_content, _ = rag.context_for(subject, chapter, concept)
        rag_text = rag_content.strip() or "(No NCERT content found — use standard CBSE Class 10 knowledge, do not invent specifics.)"

        # 1. CORE plan + lesson (English)
        try:
            core: _CorePlan = self.core_chain.invoke({
                "subject": subject, "chapter": chapter, "concept": concept,
                "mastery": mastery, "level": level,
                "quiz_responses": quiz_responses or "(none)",
                "rag": rag_text,
            })
        except Exception as e:
            note = ("The tutor needs a working HuggingFace LLM (set HF_API_TOKEN in "
                    "prototype/.env). " if not self.using_llm
                    else f"The model returned content that couldn't be parsed ({type(e).__name__}). "
                         "Try again or lower the quiz size. ")
            return TutorResponse(
                student_analysis=StudentAnalysis(level=level),
                learning_path=[],
                lesson=Lesson(concept=concept, english_explanation=note),
                quiz=[],
                recommendations=Recommendations(next_lesson=concept),
            )

        # 2. Telugu translation of the explanation (reliable, separate call)
        if language in ("telugu", "both") and self.using_llm and core.lesson.english_explanation:
            try:
                core.lesson.telugu_explanation = self.translate_chain.invoke(
                    {"text": core.lesson.english_explanation}
                ).strip()
            except Exception:
                core.lesson.telugu_explanation = ""

        # 3. Adaptive quiz (separate call keeps JSON small)
        quiz_items: List[QuizItem] = []
        if with_quiz:
            quiz_items = self.make_quiz(subject, chapter, concept, mastery,
                                        num_questions, language, q_types=q_types)

        return TutorResponse(
            student_analysis=core.student_analysis,
            learning_path=core.learning_path,
            lesson=core.lesson,
            quiz=quiz_items,
            recommendations=core.recommendations,
        )

    # ── Quiz generation (reused by generate + re-attempts) ─────────────────────
    BATCH = 8   # questions per LLM call (keeps each JSON small & reliable)

    def make_quiz(self, subject: str, chapter: str, concept: str,
                  mastery: float, num_questions: int = 10,
                  language: str = "english", rag_content: Optional[str] = None,
                  q_types: Optional[List[str]] = None) -> List[QuizItem]:
        q_types = q_types or ["MCQ"]
        num_questions = max(1, min(int(num_questions), 100))   # cap at 100
        types_str = ", ".join(q_types)

        # PDF-first grounding covering the concept + its prerequisites.
        prereqs = curriculum.prerequisites(subject, chapter, concept)
        if rag_content is None:
            rag_content, _ = rag.grounding(subject, chapter, concept,
                                           extra_terms=" ".join(prereqs[-2:]), k=5)
        rag_text = (rag_content or "").strip() or "(No matching content; use standard CBSE Class 10 knowledge.)"

        # Generate in batches so large papers (up to 100) stay reliable.
        collected: List[QuizItem] = []
        guard = 0
        while len(collected) < num_questions and guard < (num_questions // self.BATCH) + 6:
            guard += 1
            take = min(self.BATCH, num_questions - len(collected))
            dist = quiz_distribution(mastery, take)
            dist_str = ", ".join(f"{v} {k}" for k, v in dist.items() if v)
            try:
                ql: _QuizList = self.quiz_chain.invoke({
                    "subject": subject, "chapter": chapter, "concept": concept,
                    "mastery": mastery, "level": level_for(mastery), "dist": dist_str,
                    "prereqs": ", ".join(prereqs) or "(none)", "rag": rag_text,
                    "n": take, "types": types_str,
                })
            except Exception:
                break
            if not ql.quiz:
                break
            # Keep ONLY the types the student selected — classify by structure,
            # since the model often mislabels (or ignores) the requested types.
            for q in ql.quiz:
                ct = _classify_type(q)
                if ct in q_types:
                    q.type = ct
                    collected.append(q)
            if len(collected) >= num_questions:
                break

        collected = collected[:num_questions]
        if language in ("telugu", "both") and self.using_llm:
            collected = [self._localize_item(q, language) for q in collected]
        return collected

    # ── Translate one quiz item into Telugu / bilingual ────────────────────────
    def _translate_one(self, text: str) -> str:
        """Reliable single-string translation (same path used for the lesson)."""
        if not text or not text.strip():
            return text
        try:
            return self.translate_chain.invoke({"text": text}).strip() or text
        except Exception:
            return text

    @staticmethod
    def _looks_untranslated(src: str, out: str) -> bool:
        """True if the 'translation' is empty or basically still the English text."""
        if not out or out.strip().lower() == src.strip().lower():
            return True
        # No Telugu characters at all (Unicode block 0C00–0C7F) for non-trivial text
        if len(src.strip()) > 3 and not any("ఀ" <= ch <= "౿" for ch in out):
            return True
        return False

    def _translate_lines(self, lines: List[str]) -> List[str]:
        """Translate lines to Telugu. Fast path: one marker-batched call. Any
        segment that is missing or comes back still-English is repaired with an
        individual translation call, so the output is reliably Telugu."""
        if not lines:
            return lines
        found = {}
        try:
            tagged = "\n".join(f"<<{i + 1}>> {l}" for i, l in enumerate(lines))
            out = self.translate_lines_chain.invoke({"lines": tagged})
            found = {int(m.group(1)): m.group(2).strip() for m in _MARK_RE.finditer(out)}
        except Exception:
            found = {}

        result = []
        for i, src in enumerate(lines):
            cand = found.get(i + 1, "")
            if self._looks_untranslated(src, cand):
                cand = self._translate_one(src)   # individual repair
            result.append(cand or src)
        return result

    def _localize_item(self, q: QuizItem, language: str) -> QuizItem:
        letters, en_texts = [], []
        for opt in q.options:
            lt, tx = _split_option(opt)
            letters.append(lt)
            en_texts.append(tx)

        # One translation call per question: [question, *options, explanation]
        src = [q.question] + en_texts + [q.explanation or ""]
        tel = self._translate_lines(src)
        te_q, te_opts, te_expl = tel[0], tel[1:1 + len(en_texts)], tel[-1]

        if language == "telugu":
            question = te_q
            options = [f"{letters[i] or chr(65 + i)}) {te_opts[i]}" for i in range(len(en_texts))]
            explanation = te_expl
        else:  # both
            question = f"{q.question}  /  {te_q}"
            options = [f"{letters[i] or chr(65 + i)}) {en_texts[i]} / {te_opts[i]}"
                       for i in range(len(en_texts))]
            explanation = f"{q.explanation} / {te_expl}" if q.explanation else te_expl

        return QuizItem(
            question=question, type=q.type, difficulty=q.difficulty,
            concept_tested=q.concept_tested, options=options,
            answer=q.answer, explanation=explanation,
        )

    # ── Grading (auto-grades MCQ + MSQ; Short/Long shown for self-review) ───────
    @staticmethod
    def grade(quiz: List[QuizItem], answers: Dict[int, str]) -> Dict:
        graded, scored, correct = [], 0, 0
        for i, q in enumerate(quiz):
            t = q.type.upper()
            given_raw = answers.get(i, "") or ""
            ok = None
            if t == "MCQ" and q.options:
                scored += 1
                ok = _letters(given_raw) == _letters(q.answer) and len(_letters(q.answer)) == 1
                correct += int(ok)
            elif t == "MSQ" and q.options:
                scored += 1
                ok = (_letters(given_raw) == _letters(q.answer)) and bool(_letters(q.answer))
                correct += int(ok)
            graded.append({
                "question": q.question, "type": q.type, "difficulty": q.difficulty,
                "concept": q.concept_tested, "given": given_raw,
                "correct_answer": q.answer, "is_correct": ok,
                "explanation": q.explanation,
            })
        pct = round(correct / scored * 100, 1) if scored else 0.0
        return {"correct": correct, "scored": scored, "percentage": pct, "results": graded}

    # ── Score-gated progression ────────────────────────────────────────────────
    @staticmethod
    def progress_decision(graded: Dict, subject: str, chapter: str,
                          concept: str) -> Dict:
        """Decide what happens after a quiz.

        score >= PASS_THRESHOLD -> advance to the next concept in the module.
        score <  PASS_THRESHOLD -> re-attempt; recommend reviewing the concepts
                                   tied to the missed questions + prerequisites.
        """
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

        # Failed -> build review topics from missed questions + prerequisites.
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
