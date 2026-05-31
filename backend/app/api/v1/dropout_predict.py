from fastapi import APIRouter

from app.schemas.dropout import (
    StudentInput
)

from app.services.dropout_service import (
    predict_student_risk
)

router = APIRouter()


@router.post(
    "/predict"
)
def predict_dropout(
    student: StudentInput
):

    return predict_student_risk(
        student.model_dump()
    )