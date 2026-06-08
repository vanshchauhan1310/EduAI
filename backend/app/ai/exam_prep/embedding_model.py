# app/ai/exam_prep/embedding_model.py

from functools import lru_cache

from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    Shared SentenceTransformer instance.

    Loaded once per process and reused — instantiating fresh per request
    re-downloads/re-checks model files from the HF Hub each time, adding
    ~15s of latency and risking client-side timeouts.
    """
    return SentenceTransformer(
        EMBEDDING_MODEL_NAME,
        local_files_only=True,
    )
