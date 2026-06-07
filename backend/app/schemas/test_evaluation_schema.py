from app.schemas.evaluation import (
    EvaluationRequest
)

req = EvaluationRequest(
    question_id="123",
    student_answer="test"
)

print(req)