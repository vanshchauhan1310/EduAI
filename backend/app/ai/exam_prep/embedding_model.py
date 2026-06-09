# app/ai/exam_prep/embedding_model.py
#
# Uses fastembed (ONNX Runtime) instead of sentence-transformers (PyTorch).
# Memory footprint: ~75 MB vs ~390 MB — required for Render free tier (512 MB).

from functools import lru_cache

import numpy as np

EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"  # 384-dim, same as all-MiniLM-L6-v2


def cos_sim(a, b) -> np.ndarray:
    """Cosine similarity between row vectors. Returns shape (len(a), len(b))."""
    a = np.atleast_2d(np.asarray(a, dtype=np.float32))
    b = np.atleast_2d(np.asarray(b, dtype=np.float32))
    a = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-9)
    b = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-9)
    return a @ b.T


class _FastEmbedWrapper:
    """
    Drop-in replacement for SentenceTransformer with the same .encode() signature.
    Backed by fastembed (ONNX) so it does not require PyTorch.
    """

    def __init__(self):
        from fastembed import TextEmbedding
        self._model = TextEmbedding(model_name=EMBEDDING_MODEL_NAME)

    def encode(
        self,
        sentences,
        normalize_embeddings: bool = True,
        show_progress_bar: bool = False,
        convert_to_tensor: bool = False,
        **_kwargs,
    ) -> np.ndarray:
        single = isinstance(sentences, str)
        if single:
            sentences = [sentences]
        embeddings = np.array(list(self._model.embed(sentences)), dtype=np.float32)
        if normalize_embeddings:
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / np.where(norms == 0, 1, norms)
        # convert_to_tensor=True was used for torch tensors; numpy arrays work the same way
        # for cos_sim and .item() / .max() calls
        return embeddings[0] if single else embeddings


@lru_cache(maxsize=1)
def get_embedding_model() -> _FastEmbedWrapper:
    """
    Lazily-loaded singleton. First call downloads the ONNX model (~25 MB) and
    caches it under ~/.cache/fastembed/. Subsequent calls return instantly.
    """
    return _FastEmbedWrapper()
