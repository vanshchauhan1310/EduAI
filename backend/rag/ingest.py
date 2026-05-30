"""
Automated PDF Ingestion Pipeline (Knowledge Base Builder)
=========================================================
NO manual JSON. NO manual chapters/concepts.
Any NCERT PDF dropped in becomes part of the knowledge base automatically.

Pipeline:
    upload_pdf  →  step1_extract_text   (PyPDFLoader)
                →  step2_create_chunks   (RecursiveCharacterTextSplitter 1000/200)
                →  step3_generate_embeddings (BAAI/bge-small-en-v1.5)
                →  step4_store_in_chromadb  (persistent local vector DB)

Every chunk is stored with metadata: {subject, source, page}.
"""

import os
import logging
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────
CHROMA_DB_PATH  = os.getenv("CHROMA_DB_PATH", "./chroma_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
COLLECTION_NAME = "edusakhi_knowledge_base"

CHUNK_SIZE    = 1000
CHUNK_OVERLAP = 200
BATCH_SIZE    = 500     # upsert in batches for memory safety

# ── Lazy singletons (heavy objects, created once) ─────────────────────────────
_chroma_client = None
_collection    = None
_embed_model   = None


def _get_chroma_collection():
    """Return (and lazily create) the persistent ChromaDB collection."""
    global _chroma_client, _collection
    if _collection is None:
        import chromadb
        _chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        _collection = _chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _get_embed_model():
    """Return (and lazily load) the sentence-transformer embedding model."""
    global _embed_model
    if _embed_model is None:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        _embed_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embed_model


# ── Step 1: Extract text ──────────────────────────────────────────────────────
def step1_extract_text(pdf_path: str) -> List:
    """Extract text page-by-page using LangChain's PyPDFLoader."""
    from langchain_community.document_loaders import PyPDFLoader
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()   # one Document per page
    logger.info(f"Extracted {len(pages)} pages from {pdf_path}")
    return pages


# ── Step 2: Chunk ─────────────────────────────────────────────────────────────
def step2_create_chunks(pages: List) -> List:
    """Split pages into overlapping chunks."""
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(pages)
    logger.info(f"Created {len(chunks)} chunks")
    return chunks


# ── Step 3: Embeddings ────────────────────────────────────────────────────────
def step3_generate_embeddings(chunks: List) -> List[List[float]]:
    """Generate L2-normalised embeddings for cosine similarity."""
    model = _get_embed_model()
    texts = [c.page_content for c in chunks]
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,   # L2 normalise → cosine similarity
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    return embeddings.tolist()


# ── Step 4: Store in ChromaDB ─────────────────────────────────────────────────
def step4_store_in_chromadb(
    chunks:     List,
    embeddings: List[List[float]],
    subject:    str,
    pdf_path:   str,
) -> int:
    """Upsert chunks + embeddings + metadata into ChromaDB (in batches)."""
    collection = _get_chroma_collection()
    source = os.path.basename(pdf_path)

    ids, docs, metas, embs = [], [], [], []
    for i, chunk in enumerate(chunks):
        page = chunk.metadata.get("page", 0) + 1   # 1-indexed
        ids.append(f"{source}-{i}")
        docs.append(chunk.page_content)
        metas.append({"subject": subject, "source": source, "page": page})
        embs.append(embeddings[i])

    stored = 0
    for start in range(0, len(ids), BATCH_SIZE):
        end = start + BATCH_SIZE
        collection.upsert(
            ids=ids[start:end],
            documents=docs[start:end],
            metadatas=metas[start:end],
            embeddings=embs[start:end],
        )
        stored += len(ids[start:end])

    logger.info(f"Stored {stored} chunks for subject={subject}")
    return stored


# ── Public entry point ────────────────────────────────────────────────────────
def ingest_pdf(pdf_path: str, subject: str) -> Dict:
    """
    Run the full ingestion pipeline on one PDF.

    Parameters
    ----------
    pdf_path : path to the uploaded NCERT PDF
    subject  : "Physics" | "Chemistry" | "Mathematics" | ...
    """
    if not os.path.exists(pdf_path):
        return {"success": False, "error": f"File not found: {pdf_path}"}

    try:
        pages      = step1_extract_text(pdf_path)
        chunks     = step2_create_chunks(pages)
        embeddings = step3_generate_embeddings(chunks)
        stored     = step4_store_in_chromadb(chunks, embeddings, subject, pdf_path)

        return {
            "success":        True,
            "subject":        subject,
            "source":         os.path.basename(pdf_path),
            "pages":          len(pages),
            "chunks_created": len(chunks),
            "chunks_stored":  stored,
        }
    except Exception as e:
        logger.exception("Ingestion failed")
        return {"success": False, "error": str(e)}


# ── Stats ─────────────────────────────────────────────────────────────────────
def get_ingestion_stats() -> Dict:
    """Return per-subject chunk counts in the knowledge base."""
    collection = _get_chroma_collection()
    total = collection.count()

    # Pull metadata to count by subject (ok for moderate sizes).
    by_subject: Dict[str, int] = {}
    if total:
        data = collection.get(include=["metadatas"])
        for meta in data.get("metadatas", []):
            subj = (meta or {}).get("subject", "unknown")
            by_subject[subj] = by_subject.get(subj, 0) + 1

    return {
        "total_chunks": total,
        "by_subject":   by_subject,
        "collection":   COLLECTION_NAME,
    }
