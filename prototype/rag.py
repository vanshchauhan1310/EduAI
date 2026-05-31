"""
RAG retriever (TF-IDF over the Class 10 knowledge base + ingested PDFs)
======================================================================
Indexes two sources and retrieves the most relevant passages for a query:
  1. curated concept notes (knowledge_base.NOTES)
  2. chunks parsed from uploaded PDFs (db.KBChunk)

The retrieved text is passed to the tutor as grounding content. Pure-Python
TF-IDF (cosine) — no heavy embedding deps. Call rebuild_index() after ingesting
a new PDF so its chunks become searchable.
"""

import math
import re
from collections import Counter
from typing import Dict, List, Tuple

from knowledge_base import NOTES

_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = {
    "the", "a", "an", "of", "to", "in", "is", "are", "and", "or", "it", "its",
    "for", "on", "as", "by", "with", "from", "between", "two", "this", "that",
}


def _tokens(text: str) -> List[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in _STOP and len(t) > 1]


class TfidfRetriever:
    def __init__(self, docs: List[Dict]):
        # docs: [{"label","text","kind"}]
        self.docs = docs
        toks = [_tokens(d["label"] + " " + d["text"]) for d in docs]
        n = max(len(toks), 1)
        df = Counter()
        for t in toks:
            for term in set(t):
                df[term] += 1
        self.idf = {term: math.log(n / (1 + c)) + 1.0 for term, c in df.items()}
        self.vectors = [self._vectorize(t) for t in toks]

    def _vectorize(self, toks: List[str]) -> Dict[str, float]:
        tf = Counter(toks)
        vec = {term: freq * self.idf.get(term, 0.0) for term, freq in tf.items()}
        norm = math.sqrt(sum(w * w for w in vec.values())) or 1.0
        return {term: w / norm for term, w in vec.items()}

    @staticmethod
    def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
        small, big = (a, b) if len(a) < len(b) else (b, a)
        return sum(w * big.get(term, 0.0) for term, w in small.items())

    def retrieve(self, query: str, k: int = 3, kind: str = None,
                 subject: str = None, chapter: str = None) -> List[Dict]:
        if not self.docs:
            return []
        qvec = self._vectorize(_tokens(query))
        scored = []
        for i, d in enumerate(self.docs):
            if kind and d.get("kind") != kind:
                continue
            if subject and d.get("subject") and d["subject"] != subject:
                continue
            if chapter and d.get("chapter") and d["chapter"] != chapter:
                continue
            scored.append({
                "concept": d["label"], "text": d["text"],
                "kind": d.get("kind", "note"),
                "score": round(self._cosine(qvec, self.vectors[i]), 4),
            })
        scored.sort(key=lambda d: d["score"], reverse=True)
        return [s for s in scored if s["score"] > 0][:k]


def _build_corpus() -> List[Dict]:
    """Curated notes + any PDF chunks stored in the DB."""
    docs: List[Dict] = [
        {"label": concept, "text": text, "kind": "note"}
        for concept, text in NOTES.items()
    ]
    try:
        import db as store
        session = store.SessionLocal()
        try:
            for c in store.all_chunks(session):
                docs.append({
                    "label": f"{c.source} (p{c.page})",
                    "text": c.text, "kind": "pdf",
                    "subject": c.subject, "chapter": c.chapter,
                })
        finally:
            session.close()
    except Exception:
        pass  # DB/table not ready yet — notes only
    return docs


_retriever = TfidfRetriever(_build_corpus())


def rebuild_index() -> int:
    """Re-read notes + PDF chunks. Call after ingesting a PDF. Returns doc count."""
    global _retriever
    _retriever = TfidfRetriever(_build_corpus())
    return len(_retriever.docs)


def retrieve(query: str, k: int = 3) -> List[Dict]:
    return _retriever.retrieve(query, k)


def grounding(subject: str, chapter: str, concept: str,
              extra_terms: str = "", k: int = 5) -> Tuple[str, List[Dict]]:
    """PDF-first grounding: if PDFs are ingested for this subject/chapter, their
    most relevant chunks lead, then curated notes fill the rest. This makes the
    tutor prefer uploaded PDF content when it exists."""
    query = f"{concept} {extra_terms} {chapter} {subject}".strip()
    # Relevance-based (NOT locked to the chapter tag) so a full-book PDF surfaces
    # the right pages for any concept, regardless of how it was tagged at upload.
    pdf_hits = _retriever.retrieve(query, k=max(2, k // 2), kind="pdf")
    other = _retriever.retrieve(query, k=k)
    merged, seen = [], set()
    for h in pdf_hits + other:           # PDF chunks first
        key = (h["concept"], h["text"][:40])
        if key in seen:
            continue
        seen.add(key)
        merged.append(h)
    merged = merged[:k]
    context = "\n".join(f"[{h['concept']}] {h['text']}" for h in merged)
    return context, merged


def context_for(subject: str, chapter: str, concept: str, k: int = 4) -> Tuple[str, List[Dict]]:
    """Backward-compatible alias — PDF-first grounding for a concept."""
    return grounding(subject, chapter, concept, k=k)
