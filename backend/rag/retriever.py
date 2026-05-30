"""
RAG Retriever
=============
Semantic search over the ChromaDB knowledge base built by `ingest.py`.
Shares the same embedding model and collection (single unified collection,
filtered by `subject` metadata at query time).
"""

import logging
from typing import Dict, List, Optional

from rag.ingest import _get_chroma_collection, _get_embed_model

logger = logging.getLogger(__name__)


class RAGRetriever:
    """Retrieve relevant NCERT passages for a query."""

    def __init__(self, top_k: int = 5):
        self.top_k = top_k

    # ── Core retrieval ────────────────────────────────────────────────────────
    def retrieve(
        self,
        query:   str,
        subject: Optional[str] = None,
        top_k:   Optional[int] = None,
    ) -> List[Dict]:
        """
        Return the most relevant chunks for a query.

        Each result: {text, subject, source, page, relevance_score}
        """
        k = top_k or self.top_k
        try:
            collection = _get_chroma_collection()
            if collection.count() == 0:
                return []

            model = _get_embed_model()
            q_emb = model.encode(
                [query], normalize_embeddings=True, convert_to_numpy=True
            ).tolist()

            where = {"subject": subject} if subject else None
            results = collection.query(
                query_embeddings=q_emb,
                n_results=k,
                where=where,
                include=["documents", "metadatas", "distances"],
            )

            out: List[Dict] = []
            docs  = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            dists = results.get("distances", [[]])[0]

            for doc, meta, dist in zip(docs, metas, dists):
                meta = meta or {}
                out.append({
                    "text":            doc,
                    "subject":         meta.get("subject", ""),
                    "source":          meta.get("source", ""),
                    "page":            meta.get("page", 0),
                    # cosine distance → similarity
                    "relevance_score": round(1.0 - dist, 4),
                })
            return out

        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            return []

    # ── Formatted context for LLM prompts ─────────────────────────────────────
    def get_context(
        self,
        query:   str,
        subject: Optional[str] = None,
        top_k:   Optional[int] = None,
    ) -> str:
        """Return retrieved chunks as a single formatted context string."""
        chunks = self.retrieve(query, subject=subject, top_k=top_k)
        blocks = [
            f"[Source: {c['source']} | Page: {c['page']}]\n{c['text']}"
            for c in chunks
        ]
        return "\n\n".join(blocks)

    # ── Citation sources only ─────────────────────────────────────────────────
    def get_sources(
        self,
        query:   str,
        subject: Optional[str] = None,
        top_k:   Optional[int] = None,
    ) -> List[Dict]:
        """Return source/page metadata only (for citation display)."""
        chunks = self.retrieve(query, subject=subject, top_k=top_k)
        seen, sources = set(), []
        for c in chunks:
            key = (c["source"], c["page"])
            if key in seen:
                continue
            seen.add(key)
            sources.append({
                "source":          c["source"],
                "page":            c["page"],
                "subject":         c["subject"],
                "relevance_score": c["relevance_score"],
            })
        return sources
