"""
AI Tutor – EduSakhi
====================
Answers student questions and explains concepts in both English and Telugu
using a Hugging Face LLM backed by RAG-retrieved NCERT content.

Model priority (configure via HF_MODEL env var):
    1. Qwen/Qwen3-8B
    2. meta-llama/Llama-3.1-8B-Instruct
    3. google/gemma-3-4b-it

The `huggingface_hub` import is lazy so the rest of the platform runs even when
the LLM stack isn't installed — the tutor then returns a graceful fallback.
"""

import os
import logging
from typing import Dict, Optional

from dotenv import load_dotenv

from rag.retriever import RAGRetriever

load_dotenv()
logger = logging.getLogger(__name__)

HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
HF_MODEL     = os.getenv("HF_MODEL", "Qwen/Qwen3-8B")


# ── Singleton LLM client ──────────────────────────────────────────────────────
_client = None


def get_llm_client():
    """Lazily create the HuggingFace InferenceClient (imported on demand)."""
    global _client
    if _client is None:
        from huggingface_hub import InferenceClient  # lazy import
        _client = InferenceClient(
            model=HF_MODEL,
            token=HF_API_TOKEN if HF_API_TOKEN else None,
        )
    return _client


# ── AI Tutor ──────────────────────────────────────────────────────────────────
class AITutor:
    """
    Explains concepts and answers student questions with NCERT-grounded context.

    All responses include both English and Telugu explanations.
    """

    def __init__(self):
        self.retriever = RAGRetriever(top_k=5)

    # ── Concept explanation ───────────────────────────────────────────────────
    def explain_concept(
        self,
        concept:  str,
        subject:  str,
        chapter:  str = "",
        language: str = "both",          # "english" | "telugu" | "both"
    ) -> Dict:
        """
        Explain a concept using RAG-retrieved NCERT context.

        Steps
        -----
        1. Retrieve relevant NCERT passages from ChromaDB.
        2. Pass them as context to the LLM.
        3. Parse and return structured English + Telugu explanation.
        """
        # ── Step 1: RAG retrieval ─────────────────────────────────────────────
        query   = f"{concept} {chapter} {subject}"
        context = self.retriever.get_context(query, subject=subject, top_k=5)
        sources = self.retriever.get_sources(query, subject=subject, top_k=3)

        context_block = (
            f"\n\nRelevant NCERT textbook content:\n{context}\n"
            if context else ""
        )

        # ── Step 2: Build prompt ──────────────────────────────────────────────
        prompt = f"""You are EduSakhi, a friendly AI tutor for CBSE Class 10 students in India.

A student is studying {subject} and wants to understand: **{concept}**
{f"Chapter: {chapter}" if chapter else ""}
{context_block}

Explain {concept} in very SIMPLE language suitable for a 15-year-old student.
Use easy words. Give a real-life example they can relate to in India.

Respond EXACTLY in this format (no changes to section headings):

ENGLISH EXPLANATION:
[2-3 sentences explaining {concept} simply]

REAL-LIFE EXAMPLE:
[1 relatable real-life example from daily life in India]

TELUGU EXPLANATION:
[Same explanation in Telugu script – use simple Telugu words]

KEY POINTS:
• [Point 1]
• [Point 2]
• [Point 3]

FORMULA (if applicable):
[Any relevant formula or leave blank]"""

        # ── Step 3: Call LLM ──────────────────────────────────────────────────
        try:
            client   = get_llm_client()
            response = client.chat_completion(
                messages=[
                    {
                        "role":    "system",
                        "content": (
                            "You are EduSakhi, a helpful CBSE Class 10 tutor. "
                            "Always explain in both English and Telugu. "
                            "Use simple language. Be encouraging."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=900,
                temperature=0.7,
            )
            raw = response.choices[0].message.content
            parsed = self._parse_explanation(raw, concept)
            parsed["sources"] = sources
            return parsed

        except Exception as e:
            logger.error(f"LLM tutor error for concept={concept}: {e}")
            return self._fallback_explanation(concept, str(e))

    # ── Question answering ────────────────────────────────────────────────────
    def answer_question(
        self,
        question: str,
        subject:  str,
        chapter:  str = "",
    ) -> Dict:
        """
        Answer a student's free-text question using RAG + LLM.
        """
        context = self.retriever.get_context(question, subject=subject, top_k=5)
        sources = self.retriever.get_sources(question, subject=subject, top_k=3)

        context_block = (
            f"\n\nRelevant NCERT content:\n{context}\n"
            if context else ""
        )

        prompt = f"""You are EduSakhi, a friendly CBSE Class 10 tutor.

Student's question about {subject}{f' – {chapter}' if chapter else ''}:
"{question}"
{context_block}

Answer in simple language. Use the NCERT content above as your source.

ENGLISH ANSWER:
[Clear, simple answer in 3-5 sentences]

TELUGU ANSWER:
[Same answer in Telugu script]

REFERENCE: [Mention which chapter/concept this answer is from]"""

        try:
            client   = get_llm_client()
            response = client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are EduSakhi, a helpful CBSE tutor. Answer based on NCERT textbook content."},
                    {"role": "user",   "content": prompt},
                ],
                max_tokens=700,
                temperature=0.6,
            )
            raw = response.choices[0].message.content
            return {
                "question": question,
                "subject":  subject,
                "answer":   raw,
                "sources":  sources,
            }

        except Exception as e:
            logger.error(f"LLM Q&A error: {e}")
            return {
                "question": question,
                "subject":  subject,
                "answer":   f"Sorry, I could not answer that right now. Please try again later.\n\nError: {e}",
                "sources":  [],
                "error":    str(e),
            }

    # ── Parsing helpers ───────────────────────────────────────────────────────
    def _parse_explanation(self, raw: str, concept: str) -> Dict:
        """Parse structured LLM output into clean fields."""
        sections = {
            "english_explanation": "",
            "telugu_explanation":  "",
            "example":             "",
            "key_points":          [],
            "formula":             "",
        }

        markers = {
            "ENGLISH EXPLANATION:": "english_explanation",
            "REAL-LIFE EXAMPLE:":   "example",
            "TELUGU EXPLANATION:":  "telugu_explanation",
            "KEY POINTS:":          "key_points",
            "FORMULA":              "formula",
        }

        current_key  = None
        current_lines: list = []

        def flush():
            nonlocal current_lines
            if current_key and current_lines:
                text = "\n".join(current_lines).strip()
                if current_key == "key_points":
                    pts = [
                        l.lstrip("•-* ").strip()
                        for l in current_lines
                        if l.strip() and l.strip() not in ("", "KEY POINTS:")
                    ]
                    sections["key_points"] = [p for p in pts if p]
                else:
                    sections[current_key] = text
            current_lines = []

        for line in raw.split("\n"):
            matched = False
            for marker, key in markers.items():
                if marker in line.upper():
                    flush()
                    current_key = key
                    matched = True
                    break
            if not matched and current_key:
                current_lines.append(line)

        flush()

        return {
            "concept":              concept,
            "english_explanation":  sections["english_explanation"] or raw,
            "telugu_explanation":   sections["telugu_explanation"]  or "Telugu వివరణ అందుబాటులో లేదు.",
            "example":              sections["example"],
            "key_points":           sections["key_points"],
            "formula":              sections["formula"],
        }

    def _fallback_explanation(self, concept: str, error: str) -> Dict:
        return {
            "concept":             concept,
            "english_explanation": f"Explanation for '{concept}' is being prepared. Please try again.",
            "telugu_explanation":  f"'{concept}' వివరణ తయారు అవుతోంది. దయచేసి మళ్లీ ప్రయత్నించండి.",
            "example":             "",
            "key_points":          [],
            "formula":             "",
            "sources":             [],
            "error":               error,
        }
