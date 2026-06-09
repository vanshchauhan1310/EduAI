# app/ai/exam_prep/semantic_scorer.py

from app.ai.exam_prep.embedding_model import cos_sim

from app.ai.exam_prep.embedding_model import get_embedding_model


class SemanticScorer:
    def __init__(self):
        self.model = get_embedding_model()

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