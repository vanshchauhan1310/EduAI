from app.ai.exam_prep.answer_evaluator import (
    AnswerEvaluator
)

from app.ai.exam_prep.question_loader import (
    QuestionLoader
)


class EvaluationService:

    def __init__(self):

        self.evaluator = (
            AnswerEvaluator()
        )

    def evaluate(
        self,
        question_id: str,
        student_answer: str
    ):

        question = (
            QuestionLoader
            .get_question_by_id(
                question_id
            )
        )

        if not question:

            raise ValueError(
                f"Question {question_id} not found"
            )

        return self.evaluator.evaluate(
            student_answer=student_answer,

            sample_answer=question[
                "sample_answer"
            ],

            expected_points=question[
                "expected_points"
            ],

            max_score=question[
                "marks"
            ]
        )