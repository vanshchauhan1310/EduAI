from app.services.evaluation_service import (
    EvaluationService
)

service = EvaluationService()

result = service.evaluate(
    question_id=
    "0afe9c5a-04d8-4ce6-8d3b-87eb5249167e",

    student_answer=
    "A chemical reaction converts reactants into products."
)

print(result)