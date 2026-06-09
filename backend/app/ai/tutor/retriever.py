# app/ai/tutor/retriever.py
"""
Embedding-based RAG retriever for the AI Tutor (upgrades the prototype's pure-Python
TF-IDF `rag.py` to the shared sentence-transformers model already preloaded for
exam_prep — see app.ai.exam_prep.embedding_model.get_embedding_model()).

The corpus blends three sources, each tagged with a "concept" label used for grounding
and topic-detection in chat:
  - curated NOTES (knowledge_base.py) — always present, the seed corpus
  - shared TutorKnowledgeChunk rows (student_id IS NULL) — ingested official textbooks
  - the current student's own TutorKnowledgeChunk rows — "My Study Material"

Cosine similarity over normalized embeddings ranks chunks for `retrieve()`. `grounding()`
blends curated notes with PDF-derived chunks for a given (subject, chapter, concept) so
lesson generation stays anchored to the syllabus even when the LLM free-associates.
"""

from typing import Dict, List, Optional, Sequence

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.exam_prep.embedding_model import get_embedding_model
from app.ai.tutor.knowledge_base import NOTES
from app.models.tutor import TutorKnowledgeChunk

_TOP_K_DEFAULT = 4


class _Document:
    __slots__ = ("text", "concept", "subject", "chapter", "source", "page")

    def __init__(self, text: str, concept: str, subject: str = "", chapter: str = "",
                 source: str = "notes", page: Optional[int] = None):
        self.text = text
        self.concept = concept
        self.subject = subject
        self.chapter = chapter
        self.source = source
        self.page = page

    def as_source(self) -> Dict:
        return {
            "concept": self.concept,
            "subject": self.subject,
            "chapter": self.chapter,
            "source": self.source,
            "page": self.page,
            "text": self.text,
        }


class EmbeddingRetriever:
    """Per-student retriever instance — `rebuild()` (re)computes the corpus + embedding
    matrix from curated notes + shared chunks + this student's own chunks."""

    def __init__(self, student_id: Optional[int] = None):
        self.student_id = student_id
        self._docs: List[_Document] = []
        self._matrix: Optional[np.ndarray] = None
        self._loaded = False

    async def _load_docs(self, db: AsyncSession) -> List[_Document]:
        docs: List[_Document] = [_Document(text=text, concept=concept) for concept, text in NOTES.items()]

        stmt = select(TutorKnowledgeChunk).where(
            (TutorKnowledgeChunk.student_id.is_(None))
            | (TutorKnowledgeChunk.student_id == self.student_id)
        )
        result = await db.execute(stmt)
        for chunk in result.scalars().all():
            docs.append(_Document(
                text=chunk.text,
                concept=chunk.chapter or chunk.subject or "General",
                subject=chunk.subject or "",
                chapter=chunk.chapter or "",
                source=chunk.source or "upload",
                page=chunk.page,
            ))
        return docs

    async def rebuild(self, db: AsyncSession) -> None:
        self._docs = await self._load_docs(db)
        if not self._docs:
            self._matrix = None
            self._loaded = True
            return
        model = get_embedding_model()
        embeddings = model.encode(
            [doc.text for doc in self._docs],
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        self._matrix = np.asarray(embeddings, dtype=np.float32)
        self._loaded = True

    async def _ensure_loaded(self, db: AsyncSession) -> None:
        if not self._loaded:
            await self.rebuild(db)

    async def retrieve(self, db: AsyncSession, query: str, k: int = _TOP_K_DEFAULT) -> List[Dict]:
        """Top-k chunks for `query`, each shaped like prototype rag.py's source dicts:
        {concept, subject, chapter, source, page, text, score}."""
        await self._ensure_loaded(db)
        if self._matrix is None or not query.strip():
            return []
        model = get_embedding_model()
        query_vec = np.asarray(
            model.encode([query], normalize_embeddings=True, show_progress_bar=False),
            dtype=np.float32,
        )[0]
        scores = self._matrix @ query_vec
        top_idx = np.argsort(-scores)[:k]
        results = []
        for idx in top_idx:
            doc = self._docs[idx]
            entry = doc.as_source()
            entry["score"] = float(scores[idx])
            results.append(entry)
        return results

    async def grounding(self, db: AsyncSession, subject: str, chapter: str, concept: str,
                         k: int = _TOP_K_DEFAULT) -> List[Dict]:
        """PDF-first blend for lesson generation: prefer ingested-textbook chunks that
        match the chapter, fall back to / mix in the curated note for the concept, then
        top up with the closest semantic matches to the concept name."""
        await self._ensure_loaded(db)
        blended: List[Dict] = []
        seen_texts = set()

        def _add(doc_dict: Dict):
            text = doc_dict.get("text", "")
            if text and text not in seen_texts:
                seen_texts.add(text)
                blended.append(doc_dict)

        for doc in self._docs:
            if doc.source != "notes" and doc.chapter == chapter and len(blended) < k:
                _add(doc.as_source())

        note = NOTES.get(concept)
        if note:
            _add({"concept": concept, "subject": subject, "chapter": chapter,
                  "source": "notes", "page": None, "text": note})

        if len(blended) < k:
            for entry in await self.retrieve(db, f"{concept} {subject} {chapter}", k=k):
                if len(blended) >= k:
                    break
                _add(entry)

        return blended[:k]


_retrievers: Dict[Optional[int], EmbeddingRetriever] = {}


def get_retriever(student_id: Optional[int]) -> EmbeddingRetriever:
    """Per-student singleton — keeps "My Study Material" private while sharing the
    curated-notes + shared-chunk corpus across students."""
    retriever = _retrievers.get(student_id)
    if retriever is None:
        retriever = EmbeddingRetriever(student_id)
        _retrievers[student_id] = retriever
    return retriever


async def rebuild_index(db: AsyncSession, student_id: Optional[int]) -> None:
    """Force a re-embed for one student's retriever — call after PDF ingestion so new
    chunks are searchable immediately. Also drops the shared (student_id=None) cache so
    seeded/shared content is picked up by everyone on next use."""
    await get_retriever(student_id).rebuild(db)
    if None in _retrievers and student_id is not None:
        _retrievers[None]._loaded = False
