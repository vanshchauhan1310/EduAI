from app.ai.exam_prep.question_loader import (
    QuestionLoader
)

question = (
    QuestionLoader
    .get_question_by_number(
        "Q1"
    )
)

print(question)