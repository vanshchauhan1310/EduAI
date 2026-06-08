"""
Student chat tutor (RAG-grounded, auto-topic)
=============================================
Lets a student ask their own questions and learn interactively. The topic is
detected AUTOMATICALLY from the question via retrieval over the whole knowledge
base (curated notes + ingested PDFs) — the student doesn't pick subject/chapter.
Answers can be English, Telugu, or both, and keep short conversation history.
"""

from typing import List, Tuple

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

import rag
from llm_provider import get_chat_model, using_real_llm

_LANG = {
    "english": "Answer in clear, simple English.",
    "telugu":  "Answer ENTIRELY in simple Telugu (తెలుగు) script.",
    "both":    "Answer in simple English first, then repeat in Telugu (తెలుగు).",
}


class TutorChat:
    def __init__(self):
        self.model = get_chat_model()
        self.using_llm = using_real_llm()

    def reply(
        self,
        question: str,
        language: str = "english",
        history: List[Tuple[str, str]] = None,
    ) -> Tuple[str, str, list]:
        """Return (answer, detected_topic, sources). Topic is auto-detected."""
        # Auto-context: retrieve relevant content from the WHOLE knowledge base.
        sources = rag.retrieve(question, k=4)
        context = "\n".join(f"[{s['concept']}] {s['text']}" for s in sources)
        detected = sources[0]["concept"] if sources else "general Class 10"
        ground = context or "(No specific notes found; use standard CBSE Class 10 knowledge.)"

        system = SystemMessage(content=(
            "You are EduSakhi, a friendly CBSE Class 10 tutor (Physics, Chemistry, "
            "Mathematics) for a 15-year-old. Figure out what the student is asking and "
            "answer it using the following textbook content as your PRIMARY source; do "
            f"not invent facts beyond Class 10 level:\n{ground}\n\n"
            f"{_LANG.get(language, _LANG['english'])} Be concise and encouraging."
        ))

        msgs = [system]
        for role, content in (history or [])[-6:]:
            msgs.append(HumanMessage(content=content) if role == "user"
                        else AIMessage(content=content))
        msgs.append(HumanMessage(content=question))

        try:
            answer = self.model.invoke(msgs).content
        except Exception as e:
            answer = (f"Sorry, I couldn't answer that right now ({type(e).__name__}). "
                      "Please try again.")
        return answer, detected, sources
