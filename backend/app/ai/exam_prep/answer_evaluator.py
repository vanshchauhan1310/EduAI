# app/ai/exam_prep/answer_evaluator.py

from app.ai.exam_prep.semantic_scorer import SemanticScorer
from app.ai.exam_prep.rubiric_scorer import RubricScorer
from app.ai.exam_prep.feedback_generator import FeedbackGenerator


class AnswerEvaluator:

    def __init__(self):

        self.semantic_scorer = SemanticScorer()

        self.rubric_scorer = RubricScorer()

    def evaluate(
        self,
        student_answer: str,
        sample_answer: str,
        expected_points: list,
        max_score: int
    ):

        semantic_score = self.semantic_scorer.score(
            student_answer,
            sample_answer
        )

        rubric_result = self.rubric_scorer.score(
            student_answer,
            expected_points
        )

        rubric_score = rubric_result["coverage"]

        final_percentage = (
            semantic_score * 0.4 +
            rubric_score * 0.6
        )

        final_marks = round(
            final_percentage * max_score
        )

        feedback = FeedbackGenerator.generate(
            rubric_result["matched_points"],
            rubric_result["missing_points"]
        )

        return {

            "score": final_marks,

            "max_score": max_score,

            "semantic_similarity": round(
                semantic_score,
                2
            ),

            "rubric_coverage": round(
                rubric_score,
                2
            ),

            "matched_points":
                rubric_result["matched_points"],

            "missing_points":
                rubric_result["missing_points"],

            "feedback":
                feedback
        }