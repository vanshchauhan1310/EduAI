import uuid

from app.ai.exam_prep.llm_question_generator import (
    LLMQuestionGenerator
)


class QuestionGenerator:

    def __init__(self):

        self.llm_generator = (
            LLMQuestionGenerator()
        )

    def generate_question(
        self,
        context,
        pattern,
        difficulty,
        marks
    ):

        generated = (
            self.llm_generator
            .generate_question(
                context=context,
                difficulty=difficulty,
                marks=marks
            )
        )

        return {

            "question_id":
                str(uuid.uuid4()),

            "question_text":
                generated["question_text"],

            "sample_answer":
                generated["sample_answer"],

            "expected_points":
                generated["expected_points"],

            "pattern":
                pattern,

            "difficulty":
                difficulty,

            "marks":
                marks
        }