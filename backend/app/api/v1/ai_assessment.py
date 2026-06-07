from fastapi import (
    APIRouter,
    HTTPException
)

from app.schemas.assessment import (
    GenerateAssessmentRequest,
    GenerateAssessmentResponse,
    SubmitAssessmentRequest,
    SubmitAssessmentResponse,
    QuestionResponse,
    QuestionResult
)

from app.services.assessment_service import (
    AssessmentService
)

router = APIRouter(
    prefix="/ai-assessment",
    tags=["AI Assessment"]
)

assessment_service = (
    AssessmentService()
)


@router.post(
    "/generate",
    response_model=
    GenerateAssessmentResponse
)
async def generate_assessment(
    request:
    GenerateAssessmentRequest
):

    try:

        assessment = (
            assessment_service
            .generate_assessment(
                chapter_id=
                request.chapter_id,

                difficulty=
                request.difficulty,

                num_questions=
                request.num_questions
            )
        )

        questions = []

        for question in (
            assessment["questions"]
        ):

            questions.append(
                QuestionResponse(
                    question_id=
                    question["question_id"],

                    question_text=
                    question["question_text"],

                    marks=
                    question["marks"],

                    difficulty=
                    question["difficulty"]
                )
            )

        return (
            GenerateAssessmentResponse(
                assessment_id=
                assessment[
                    "assessment_id"
                ],

                chapter_id=
                assessment[
                    "chapter_id"
                ],

                difficulty=
                assessment[
                    "difficulty"
                ],

                total_questions=
                assessment[
                    "total_questions"
                ],

                total_marks=
                assessment[
                    "total_marks"
                ],

                questions=
                questions
            )
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post(
    "/submit",
    response_model=
    SubmitAssessmentResponse
)
async def submit_assessment(
    request:
    SubmitAssessmentRequest
):

    try:

        result = (
            assessment_service
            .submit_assessment(
                assessment_id=
                request.assessment_id,

                answers=[
                    answer.model_dump()

                    for answer in
                    request.answers
                ]
            )
        )

        results = []

        for item in (
            result["results"]
        ):

            results.append(
                QuestionResult(
                    question_id=
                    item["question_id"],

                    question_text=
                    item["question_text"],

                    score=
                    item["score"],

                    max_score=
                    item["max_score"],

                    semantic_similarity=
                    item[
                        "semantic_similarity"
                    ],

                    rubric_coverage=
                    item[
                        "rubric_coverage"
                    ],

                    feedback=
                    item["feedback"],

                    matched_points=
                    item[
                        "matched_points"
                    ],

                    missing_points=
                    item[
                        "missing_points"
                    ]
                )
            )

        return (
            SubmitAssessmentResponse(
                assessment_id=
                result[
                    "assessment_id"
                ],

                total_questions=
                result[
                    "total_questions"
                ],

                total_score=
                result[
                    "total_score"
                ],

                max_score=
                result[
                    "max_score"
                ],

                percentage=
                result[
                    "percentage"
                ],

                results=
                results
            )
        )

    except ValueError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )