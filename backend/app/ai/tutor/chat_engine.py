# app/ai/tutor/chat_engine.py
"""
Student chat tutor — RAG-grounded, auto-topic (ports prototype/chat_engine.TutorChat).

The topic is detected AUTOMATICALLY from the question via retrieval over the whole
knowledge base (curated notes + shared/personal ingested chunks) — the student doesn't
pick subject/chapter. Answers can be English, Telugu, or both, with short history.
"""

import re
from typing import Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.tutor.llm_client import get_llm_client, using_real_llm
from app.ai.tutor.retriever import get_retriever

_LANG = {
    "english": "Answer in clear, simple English.",
    "telugu": "Answer ENTIRELY in simple Telugu (తెలుగు) script.",
    "both": "Answer in simple English first, then repeat in Telugu (తెలుగు).",
}

GENERAL_TOPIC = "general Class 10"

# Matches a self-reported topic line the model is asked to end its answer with,
# e.g. "TOPIC: Mirror Formula" — lets the purple topic chip reflect what the
# answer actually covered rather than just the top RAG retrieval hit.
_TOPIC_LINE_RE = re.compile(r'(?:^|\n)\s*TOPIC:\s*(.+?)\s*$', re.IGNORECASE)


def _system(text: str) -> Dict[str, str]:
    return {"role": "system", "content": text}


def _msg(role: str, text: str) -> Dict[str, str]:
    return {"role": role, "content": text}


class TutorChat:
    def __init__(self):
        self.client = get_llm_client()
        self.using_llm = using_real_llm()

    async def reply(
        self,
        db: AsyncSession,
        student_id: Optional[int],
        question: str,
        language: str = "english",
        history: Optional[List[Tuple[str, str]]] = None,
    ) -> Tuple[str, str, List[Dict]]:
        """Returns (answer, detected_topic, sources). Topic is auto-detected from
        the top retrieval hit; falls back to GENERAL_TOPIC when nothing matches
        closely (so the service skips an irrelevant image lookup)."""
        sources = await get_retriever(student_id).retrieve(db, question, k=4)
        context = "\n".join(f"[{s['concept']}] {s['text']}" for s in sources)
        detected = sources[0]["concept"] if sources else GENERAL_TOPIC
        ground = context or "(No specific notes found; use standard CBSE Class 10 knowledge.)"

        system = _system(
            "You are EduSakhi, a friendly CBSE Class 10 tutor (Physics, Chemistry, "
            "Mathematics) for a 15-year-old. Figure out what the student is asking and "
            "answer it using the following textbook content as your PRIMARY source; do "
            f"not invent facts beyond Class 10 level:\n{ground}\n\n"
            "Just explain the concept itself — you don't need to name, list, or link "
            "to YouTube channels, videos, images or websites; the app already shows its "
            "own curated picks below your reply, so simply skip that topic entirely if "
            "asked and move on to the actual explanation.\n\n"
            "FORMATTING — the chat bubble renders markdown and LaTeX math properly, "
            "so format your answer using them correctly (and ONLY correctly — broken "
            "syntax shows up as broken):\n"
            "- Use **bold** for key terms, and '- ' or '1. ' for lists, exactly as in "
            "standard markdown. Don't use raw '#' headings inside a chat reply.\n"
            "- Write every equation, formula or chemical reaction as proper LaTeX "
            "wrapped in \\( ... \\) for inline or \\[ ... \\] for standalone math — "
            "e.g. \\( \\frac{1}{v} - \\frac{1}{u} = \\frac{1}{f} \\) or "
            "\\[ 3Fe + 4H_2O \\rightarrow Fe_3O_4 + 4H_2 \\]. "
            "Always use matching braces ({...}, never [...}) and valid commands "
            "(\\frac{a}{b}, \\rightarrow, _{2}, ^{2}, \\text{...}) — never invent or "
            "garble LaTeX commands, and never mix [ and { for the same group.\n\n"
            f"{_LANG.get(language, _LANG['english'])} Be concise and encouraging.\n\n"
            "Finally, end your reply with one extra line in EXACTLY this form (it will "
            "be removed before the student sees it, so it must reflect what your answer "
            "above is actually about):\nTOPIC: <a short 2-5 word name for the main topic "
            "your answer covers>"
        )

        messages = [system]
        for role, content in (history or [])[-6:]:
            messages.append(_msg("user" if role == "user" else "assistant", content))
        messages.append(_msg("user", question))

        try:
            answer = self.client.chat(messages, temperature=0.4, max_tokens=900)
        except Exception as exc:
            answer = (f"Sorry, I couldn't answer that right now ({type(exc).__name__}). "
                      "Please try again.")
            return answer, detected, sources

        topic_match = _TOPIC_LINE_RE.search(answer)
        if topic_match:
            self_reported = topic_match.group(1).strip().strip('.')
            if self_reported:
                detected = self_reported
            answer = _TOPIC_LINE_RE.sub('', answer).rstrip()

        return answer, detected, sources


_chat: Optional[TutorChat] = None


def get_tutor_chat() -> TutorChat:
    global _chat
    if _chat is None:
        _chat = TutorChat()
    return _chat
