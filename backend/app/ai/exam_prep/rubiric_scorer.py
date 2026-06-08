# app/ai/exam_prep/rubric_scorer.py

from typing import List, Dict

from sentence_transformers.util import cos_sim

from app.ai.exam_prep.embedding_model import get_embedding_model


class RubricScorer:

    def __init__(self):

        self.model = get_embedding_model()

        self.threshold = 0.55

    def _split_sentences(
        self,
        text: str
    ) -> List[str]:

        sentences = []

        for sentence in text.replace("\n", ".").split("."):

            sentence = sentence.strip()

            if sentence:
                sentences.append(sentence)

        return sentences

    def score(
        self,
        student_answer: str,
        expected_points: List[str]
    ) -> Dict:

        if not student_answer.strip():

            return {
                "coverage": 0.0,
                "matched_points": [],
                "missing_points": expected_points,
                "point_scores": {}
            }

        matched = []
        missing = []
        point_scores = {}

        student_sentences = self._split_sentences(
            student_answer
        )

        sentence_embeddings = self.model.encode(
            student_sentences,
            convert_to_tensor=True
        )

        for point in expected_points:

            point_embedding = self.model.encode(
                point,
                convert_to_tensor=True
            )

            similarities = cos_sim(
                point_embedding,
                sentence_embeddings
            )[0]

            best_similarity = float(
                similarities.max().item()
            )

            point_scores[point] = round(
                best_similarity,
                3
            )

            if best_similarity >= self.threshold:

                matched.append(point)

            else:

                missing.append(point)

        coverage = 0.0

        if expected_points:

            coverage = (
                len(matched)
                / len(expected_points)
            )

        return {
            "coverage": round(
                coverage,
                3
            ),
            "matched_points": matched,
            "missing_points": missing,
            "point_scores": point_scores
        }