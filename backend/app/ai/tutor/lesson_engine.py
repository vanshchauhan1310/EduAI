# app/ai/tutor/lesson_engine.py
"""
Adaptive lesson + quiz generator (ports prototype/learning_system.AdaptiveTutor).

Drops the LangChain layer (no ChatPromptTemplate/PydanticOutputParser — those add a
heavy dependency for no real benefit over plain f-string prompts + TutorLLMClient.chat
+ tolerant JSON parsing, matching the raw-requests style already used in exam_prep).
Keeps the same three-call structure for reliability on a 7B-class model:
    1. CORE  -> student_analysis + learning_path + lesson(English) + recommendations
    2. QUIZ  -> adaptive quiz, generated in batches of BATCH questions
    3. TELUGU -> line-by-line translation of the lesson + quiz (only when requested)

Returns plain dicts shaped exactly like the mobile `TutorGenerateResponse` pieces
(student_analysis/learning_path/lesson/quiz/recommendations) — see types/index.ts.
"""

import concurrent.futures
import logging
import re
from typing import Dict, List, Optional

from app.ai.tutor import curriculum
from app.ai.tutor.grading import _classify_type, quiz_distribution
from app.ai.tutor.llm_client import get_llm_client, parse_json, using_real_llm

logger = logging.getLogger(__name__)

BATCH = 10            # questions per LLM call — fits in max_tokens=2500 comfortably
TRANSLATE_BATCH = 10  # strings per translation call — smaller = faster per-batch
MAX_TRANSLATE_WORKERS = 6  # parallel translation threads

_MARK_RE = re.compile(r"<<(\d+)>>\s*(.*?)(?=(?:<<\d+>>)|\Z)", re.S)
_OPT_RE = re.compile(r"^\s*([A-Da-d])\)\s*(.*)$", re.S)
_TELUGU_RE = re.compile(r"[ఀ-౿]")

_DEFAULT_ANALYSIS = {"level": "Beginner", "strong_concepts": [], "weak_concepts": [], "misconceptions": []}
_DEFAULT_LESSON_KEYS = ("real_life_examples", "worked_examples", "common_mistakes", "revision_notes")


def _system(text: str) -> Dict[str, str]:
    return {"role": "system", "content": text}


def _user(text: str) -> Dict[str, str]:
    return {"role": "user", "content": text}


def _split_option(opt: str):
    m = _OPT_RE.match(opt)
    if m:
        return m.group(1).upper(), m.group(2).strip()
    return "", opt.strip()


def _coerce_lesson(concept: str, raw: Dict) -> Dict:
    lesson = dict(raw or {})
    lesson.setdefault("concept", concept)
    lesson.setdefault("english_explanation", "")
    lesson.setdefault("telugu_explanation", "")
    for key in _DEFAULT_LESSON_KEYS:
        value = lesson.get(key)
        lesson[key] = value if isinstance(value, list) else ([] if value in (None, "") else [str(value)])
    return lesson


def _coerce_analysis(raw: Dict) -> Dict:
    analysis = {**_DEFAULT_ANALYSIS, **(raw or {})}
    for key in ("strong_concepts", "weak_concepts", "misconceptions"):
        value = analysis.get(key)
        analysis[key] = value if isinstance(value, list) else ([] if value in (None, "") else [str(value)])
    analysis["level"] = analysis.get("level") or "Beginner"
    return analysis


def _coerce_learning_path(raw) -> List[Dict]:
    items = []
    for i, entry in enumerate(raw or []):
        if not isinstance(entry, dict):
            continue
        items.append({
            "concept": str(entry.get("concept", "")),
            "priority": int(entry.get("priority", i + 1) or i + 1),
            "reason": str(entry.get("reason", "")),
            "estimated_time": str(entry.get("estimated_time", "20 min")),
            "activity": str(entry.get("activity", "")),
        })
    return items


def _coerce_recommendations(concept: str, raw: Dict) -> Dict:
    rec = dict(raw or {})
    next_concepts = rec.get("next_concepts")
    return {
        "next_concepts": next_concepts if isinstance(next_concepts, list) else [],
        "estimated_mastery_score": float(rec.get("estimated_mastery_score", 0.0) or 0.0),
        "next_lesson": str(rec.get("next_lesson") or concept),
    }


def _coerce_quiz_item(raw: Dict) -> Optional[Dict]:
    if not isinstance(raw, dict) or not raw.get("question"):
        return None
    # LLMs sometimes return "correct_answer" instead of "answer"
    answer = raw.get("answer") or raw.get("correct_answer") or raw.get("correct") or ""
    if not answer:
        return None
    options = raw.get("options")
    item = {
        "question": str(raw["question"]),
        "type": str(raw.get("type", "")),
        "difficulty": str(raw.get("difficulty", "Medium")),
        "concept_tested": str(raw.get("concept_tested", "")),
        "options": [str(o) for o in options] if isinstance(options, list) else [],
        "answer": str(answer),
        "explanation": str(raw.get("explanation", "")),
    }
    item["type"] = _classify_type(item)
    return item


# ── Prompt builders ───────────────────────────────────────────────────────────
_CORE_SYSTEM = (
    "You are an AI-Powered Personalized Adaptive Learning Tutor for CBSE Class 10 "
    "Government School students (Physics, Chemistry, Mathematics), English & Telugu "
    "medium. You act as teacher, assessment expert and adaptive learning engine. "
    "Use the provided NCERT content as the primary source; do NOT hallucinate. "
    "Keep explanations age-appropriate for Class 10. Return ONLY valid JSON — no "
    "markdown fences, no commentary."
)

_CORE_FORMAT = (
    'Produce a JSON object with EXACTLY these keys: student_analysis, learning_path, '
    'lesson, recommendations (DO NOT include a quiz here).\n'
    '- student_analysis: {"level": "Beginner|Intermediate|Advanced", "strong_concepts": '
    '[...], "weak_concepts": [...], "misconceptions": [...]}.\n'
    '- learning_path: ordered list (weakest concept first, respect prerequisites) of '
    '{"concept", "priority" (1=highest), "reason", "estimated_time" (e.g. "20 min"), "activity"}.\n'
    '- lesson: {"concept", "english_explanation" (clear, with CBSE terminology), '
    '"real_life_examples": [...], "worked_examples": [...] (numerical for Physics/Maths), '
    '"common_mistakes": [...], "revision_notes": [...]}. Omit telugu_explanation (added later).\n'
    '- recommendations: {"next_concepts": [...], "estimated_mastery_score" (0-100), "next_lesson"}.\n'
    'Return JSON only.'
)

_QUIZ_SYSTEM = (
    "You are an expert CBSE Class 10 examiner. Generate an adaptive quiz that tests "
    "conceptual understanding (not rote). Return ONLY valid JSON — no markdown fences. "
    "Write in English."
)

_TRANSLATE_LINES_SYSTEM = (
    "You are a precise English-to-Telugu translator for CBSE Class 10 science/maths. "
    "Each segment is prefixed with a marker like <<1>>. Translate ONLY the text after "
    "each marker into simple Telugu (తెలుగు). Reproduce every marker EXACTLY, each "
    "followed by its Telugu translation. Keep numbers and math symbols (V=IR, ohms) as is. "
    "Output nothing except the markers and their translations."
)

_TRANSLATE_ONE_SYSTEM = (
    "You are a precise English-to-Telugu translator for CBSE Class 10 science/maths. "
    "Translate the text into simple, correct Telugu (తెలుగు) suitable for a 15-year-old. "
    "Output ONLY the Telugu translation."
)


def _core_prompt(subject, chapter, concept, mastery, level, quiz_responses, rag_text) -> List[Dict[str, str]]:
    human = (
        f"Subject: {subject}\nChapter: {chapter}\nConcept: {concept}\n"
        f"Student Mastery Score (0-100): {mastery}\nLearning level: {level}\n"
        f"Prior quiz responses: {quiz_responses or '(none)'}\n"
        f"Retrieved NCERT content:\n{rag_text}\n\n{_CORE_FORMAT}"
    )
    return [_system(_CORE_SYSTEM), _user(human)]


def _quiz_prompt(subject, chapter, concept, mastery, level, prereqs, rag_text, n, dist, types_str) -> List[Dict[str, str]]:
    dist_str = ", ".join(f"{v} {k}" for k, v in dist.items() if v)
    human = (
        f"Subject: {subject}\nChapter: {chapter}\nConcept: {concept}\n"
        f"Prerequisite concepts: {', '.join(prereqs) or '(none)'}\n"
        f"Mastery: {mastery} ({level}).\n"
        "Base the questions on the following NCERT / textbook content as the PRIMARY "
        "source — prefer facts, examples and numbers found here over general knowledge. "
        f"At least half the questions MUST be answerable directly from this content:\n{rag_text}\n\n"
        f"Generate EXACTLY {n} questions with this difficulty mix: {dist_str}. "
        f"EVERY question MUST be one of these types ONLY: {types_str}. Do NOT produce any "
        "other type — no Short/Long answer unless it is listed. Spread evenly across "
        "the listed types. If MCQ or MSQ is listed, those questions MUST include 4 "
        "options 'A) '..'D) '.\n"
        "Type rules:\n"
        "- MCQ: exactly 4 options 'A) '..'D) ', exactly ONE correct; answer = one letter.\n"
        "- MSQ: exactly 4 options 'A) '..'D) ', TWO OR MORE correct; answer = the correct "
        "letters comma-separated, e.g. 'A,C'.\n"
        "- Short Answer: options = []; answer = the expected answer in 1-2 sentences.\n"
        "- Long Answer: options = []; answer = a model answer in 3-5 sentences.\n"
        'Return JSON {"quiz": [ ... ]} where each item has: question, type '
        f"(one of {types_str}), difficulty (Easy|Medium|Hard), concept_tested, options, "
        "answer, explanation. Return JSON only."
    )
    return [_system(_QUIZ_SYSTEM), _user(human)]


class LessonEngine:
    def __init__(self):
        self.using_llm = using_real_llm()
        self.client = get_llm_client()

    # ── Main entry point ──────────────────────────────────────────────────────
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
    ) -> Dict:
        level = curriculum.level_for(mastery)
        rag_text = (rag_content or "").strip() or (
            "(No NCERT content found — use standard CBSE Class 10 knowledge, do not invent specifics.)"
        )

        try:
            raw = parse_json(self.client.chat(
                _core_prompt(subject, chapter, concept, mastery, level, quiz_responses, rag_text),
                temperature=0.4, max_tokens=2200,
            ))
            lesson = _coerce_lesson(concept, raw.get("lesson") or {})
            analysis = _coerce_analysis(raw.get("student_analysis") or {})
            learning_path = _coerce_learning_path(raw.get("learning_path"))
            recommendations = _coerce_recommendations(concept, raw.get("recommendations") or {})
        except Exception as exc:
            note = ("The tutor needs a working LLM provider (set HF_API_TOKEN or "
                    "NVIDIA_NIM_API_KEY in backend/.env). " if not self.using_llm
                    else f"The model returned content that couldn't be parsed ({type(exc).__name__}). "
                         "Please try again.")
            return {
                "student_analysis": {**_DEFAULT_ANALYSIS, "level": level},
                "learning_path": [],
                "lesson": _coerce_lesson(concept, {"english_explanation": note}),
                "quiz": [],
                "recommendations": _coerce_recommendations(concept, {}),
            }

        # Run lesson translation and quiz generation in parallel — they are
        # independent after the core call, so no reason to do them sequentially.
        needs_lesson_trans = (
            language in ("telugu", "both")
            and self.using_llm
            and bool(lesson["english_explanation"])
        )

        def _translate_lesson() -> str:
            try:
                result = self._translate_lines([lesson["english_explanation"]])
                return result[0] if result else ""
            except Exception:
                return ""

        def _make_quiz() -> List[Dict]:
            if not with_quiz:
                return []
            return self.make_quiz(subject, chapter, concept, mastery, num_questions,
                                  language, rag_content=rag_content, q_types=q_types)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            trans_future = ex.submit(_translate_lesson) if needs_lesson_trans else None
            quiz_future = ex.submit(_make_quiz)
            lesson["telugu_explanation"] = trans_future.result() if trans_future else ""
            quiz = quiz_future.result()

        return {
            "student_analysis": analysis,
            "learning_path": learning_path,
            "lesson": lesson,
            "quiz": quiz,
            "recommendations": recommendations,
        }

    # ── Quiz generation (also used for re-attempts) ──────────────────────────
    def make_quiz(self, subject: str, chapter: str, concept: str, mastery: float,
                  num_questions: int = 10, language: str = "english",
                  rag_content: Optional[str] = None, q_types: Optional[List[str]] = None) -> List[Dict]:
        q_types = q_types or ["MCQ"]
        num_questions = max(1, min(int(num_questions), 100))
        types_str = ", ".join(q_types)
        level = curriculum.level_for(mastery)

        prereqs = curriculum.prerequisites(subject, chapter, concept)
        rag_text = (rag_content or "").strip() or "(No matching content; use standard CBSE Class 10 knowledge.)"

        collected: List[Dict] = []
        guard = 0
        max_guard = (num_questions // BATCH) + 6
        while len(collected) < num_questions and guard < max_guard:
            guard += 1
            take = min(BATCH, num_questions - len(collected))
            dist = quiz_distribution(mastery, take)
            try:
                raw = parse_json(self.client.chat(
                    _quiz_prompt(subject, chapter, concept, mastery, level, prereqs, rag_text, take, dist, types_str),
                    temperature=0.5, max_tokens=2500,
                ))
            except Exception as exc:
                logger.warning("Quiz LLM call failed (guard=%d): %s: %s", guard, type(exc).__name__, exc)
                break
            items = raw.get("quiz")
            if not isinstance(items, list) or not items:
                logger.warning("Quiz LLM returned no items (guard=%d, raw keys=%s)", guard, list(raw.keys()))
                break
            accepted = 0
            for raw_item in items:
                item = _coerce_quiz_item(raw_item)
                if item and item["type"] in q_types:
                    collected.append(item)
                    accepted += 1
                elif item:
                    logger.debug("Quiz item filtered (type=%s not in %s)", item["type"], q_types)
            if accepted == 0:
                logger.warning("All quiz items were filtered out (guard=%d)", guard)
                break
            if len(collected) >= num_questions:
                break

        collected = collected[:num_questions]
        if language in ("telugu", "both") and self.using_llm:
            collected = self._translate_questions_only(collected, language)
        return collected

    # ── Bilingual localization ────────────────────────────────────────────────
    def _batch_localize_items(self, items: List[Dict], language: str) -> List[Dict]:
        """Translate all quiz items in bulk instead of one API call per item.

        Collects all strings across every item into a flat list, splits into
        TRANSLATE_BATCH-sized chunks (each chunk = one _translate_lines call),
        then reassembles the translated strings back into the original item shapes.
        For N MCQ questions this reduces translation calls from N to ceil(N*6/20).
        """
        if not items:
            return items

        all_strings: List[str] = []
        meta: List[tuple] = []  # (start_idx, letters, en_texts)

        for item in items:
            letters, en_texts = [], []
            for opt in item["options"]:
                lt, tx = _split_option(opt)
                letters.append(lt)
                en_texts.append(tx)
            start = len(all_strings)
            all_strings.append(item["question"])
            all_strings.extend(en_texts)
            all_strings.append(item.get("explanation") or "")
            meta.append((start, letters, en_texts))

        # Translate all batches in parallel — each batch is an independent NIM call
        batches = [all_strings[i:i + TRANSLATE_BATCH]
                   for i in range(0, len(all_strings), TRANSLATE_BATCH)]
        workers = min(len(batches), MAX_TRANSLATE_WORKERS)
        translated: List[str] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
            # executor.map preserves input order, so concatenating results is safe
            for batch_result in ex.map(self._translate_lines, batches):
                translated.extend(batch_result)

        # Reconstruct items using the pre-recorded offsets
        result = []
        for item, (start, letters, en_texts) in zip(items, meta):
            n = len(en_texts)
            te_q = translated[start]
            te_opts = translated[start + 1: start + 1 + n]
            te_expl = translated[start + 1 + n]

            if language == "telugu":
                question = te_q
                options = [f"{letters[j] or chr(65 + j)}) {te_opts[j]}" for j in range(n)]
                explanation = te_expl
            else:  # both
                question = f"{item['question']}  /  {te_q}"
                options = [f"{letters[j] or chr(65 + j)}) {en_texts[j]} / {te_opts[j]}" for j in range(n)]
                explanation = f"{item['explanation']} / {te_expl}" if item.get("explanation") else te_expl

            result.append({**item, "question": question, "options": options, "explanation": explanation})
        return result

    def _translate_one(self, text: str) -> str:
        if not text or not text.strip():
            return text
        try:
            out = self.client.chat(
                [_system(_TRANSLATE_ONE_SYSTEM), _user(text)],
                temperature=0.2, max_tokens=800,
            ).strip()
            return out or text
        except Exception:
            return text

    @staticmethod
    def _looks_untranslated(src: str, out: str) -> bool:
        if not out or out.strip().lower() == src.strip().lower():
            return True
        if len(src.strip()) > 3 and not _TELUGU_RE.search(out):
            return True
        return False

    def _translate_lines(self, lines: List[str]) -> List[str]:
        """Marker-batched translation with per-line repair for anything that comes
        back empty or still-English — keeps output reliably Telugu."""
        if not lines:
            return lines
        found = {}
        try:
            tagged = "\n".join(f"<<{i + 1}>> {line}" for i, line in enumerate(lines))
            out = self.client.chat(
                [_system(_TRANSLATE_LINES_SYSTEM), _user(tagged)],
                temperature=0.2, max_tokens=len(lines) * 60,  # ~60 tokens per line
            )
            found = {int(m.group(1)): m.group(2).strip() for m in _MARK_RE.finditer(out)}
        except Exception:
            found = {}

        result = []
        for i, src in enumerate(lines):
            cand = found.get(i + 1, "")
            if self._looks_untranslated(src, cand):
                cand = self._translate_one(src)
            result.append(cand or src)
        return result

    def _translate_questions_only(self, items: List[Dict], language: str) -> List[Dict]:
        """Translate only the question text — options and explanations stay in English.

        For 10 MCQ questions this is 10 strings (1 batch) instead of 60 strings (6 batches),
        reducing NIM calls from 6 to 1 and cutting translation time from ~120s to ~15s.
        Options are usually formulas, numbers, or short phrases that don't need translation.
        """
        if not items:
            return items
        questions = [item["question"] for item in items]
        batches = [questions[i:i + TRANSLATE_BATCH] for i in range(0, len(questions), TRANSLATE_BATCH)]
        workers = min(len(batches), MAX_TRANSLATE_WORKERS)
        translated_qs: List[str] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
            for batch_result in ex.map(self._translate_lines, batches):
                translated_qs.extend(batch_result)
        result = []
        for item, te_q in zip(items, translated_qs):
            if language == "telugu":
                updated_q = te_q
            else:  # both
                updated_q = f"{item['question']}  /  {te_q}"
            result.append({**item, "question": updated_q})
        return result

    def _localize_item(self, item: Dict, language: str) -> Dict:
        letters, en_texts = [], []
        for opt in item["options"]:
            lt, tx = _split_option(opt)
            letters.append(lt)
            en_texts.append(tx)

        src = [item["question"]] + en_texts + [item.get("explanation") or ""]
        translated = self._translate_lines(src)
        te_q, te_opts, te_expl = translated[0], translated[1:1 + len(en_texts)], translated[-1]

        if language == "telugu":
            question = te_q
            options = [f"{letters[i] or chr(65 + i)}) {te_opts[i]}" for i in range(len(en_texts))]
            explanation = te_expl
        else:  # both
            question = f"{item['question']}  /  {te_q}"
            options = [f"{letters[i] or chr(65 + i)}) {en_texts[i]} / {te_opts[i]}"
                       for i in range(len(en_texts))]
            explanation = f"{item['explanation']} / {te_expl}" if item.get("explanation") else te_expl

        return {**item, "question": question, "options": options, "explanation": explanation}


_engine: Optional[LessonEngine] = None


def get_lesson_engine() -> LessonEngine:
    global _engine
    if _engine is None:
        _engine = LessonEngine()
    return _engine
