# app/ai/exam_prep/semantic_scorer.py

from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim


class SemanticScorer:
    def __init__(self):
        self.model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

    def score(
        self,
        student_answer: str,
        sample_answer: str
    ) -> float:

        if not student_answer.strip():
            return 0.0

        emb1 = self.model.encode(
            student_answer,
            convert_to_tensor=True
        )

        emb2 = self.model.encode(
            sample_answer,
            convert_to_tensor=True
        )

        similarity = cos_sim(
            emb1,
            emb2
        ).item()

        return max(0.0, similarity)