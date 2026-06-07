from pathlib import Path
from typing import Dict, List

from app.ai.exam_prep.answer_evaluator import (
    AnswerEvaluator
)

from app.ai.exam_prep.assessment_generator import (
    AssessmentGenerator
)

from app.ai.exam_prep.assessment_store import (
    AssessmentStore
)


class AssessmentService:

    def __init__(self):

        self.generator = (
            AssessmentGenerator()
        )

        self.evaluator = (
            AnswerEvaluator()
        )

        self.knowledge_base_dir = (
            Path("data/knowledge_base")
        )

        self.pyq_database_dir = (
            Path("data/pyq_database")
        )

        self.pattern_library_dir = (
            Path("data/pattern_library")
        )

    def generate_assessment(
        self,
        chapter_id: str,
        difficulty: str,
        num_questions: int
    ) -> Dict:

        knowledge_base_path = (
            self.knowledge_base_dir
            / f"{chapter_id}.json"
        )

        pyq_database_path = (
            self.pyq_database_dir
            / f"{chapter_id}_pyq.json"
        )

        pattern_library_path = (
            self.pattern_library_dir
            / f"{chapter_id}_patterns.json"
        )

        if not knowledge_base_path.exists():

            raise FileNotFoundError(
                f"Knowledge base not found: "
                f"{knowledge_base_path}"
            )

        if not pyq_database_path.exists():

            raise FileNotFoundError(
                f"PYQ database not found: "
                f"{pyq_database_path}"
            )

        if not pattern_library_path.exists():

            raise FileNotFoundError(
                f"Pattern library not found: "
                f"{pattern_library_path}"
            )

        assessment = (
            self.generator.generate_assessment(
                chapter_id=chapter_id,

                knowledge_base_path=
                knowledge_base_path,

                pyq_database_path=
                pyq_database_path,

                pattern_library_path=
                pattern_library_path,

                difficulty=difficulty,

                num_questions=num_questions
            )
        )

        AssessmentStore.save_assessment(
            assessment
        )

        return assessment

    def submit_assessment(
        self,
        assessment_id: str,
        answers: List[Dict]
    ) -> Dict:

        assessment = (
            AssessmentStore.load_assessment(
                assessment_id
            )
        )

        if not assessment:

            raise ValueError(
                f"Assessment "
                f"{assessment_id} "
                f"not found"
            )

        question_lookup = {

            question["question_id"]: question

            for question in
            assessment["questions"]
        }

        results = []

        total_score = 0

        total_max_score = 0

        for answer in answers:

            question_id = answer.get(
                "question_id"
            )

            student_answer = answer.get(
                "answer",
                ""
            )

            question = (
                question_lookup.get(
                    question_id
                )
            )

            if not question:

                continue

            evaluation = (
                self.evaluator.evaluate(
                    student_answer=
                    student_answer,

                    sample_answer=
                    question[
                        "sample_answer"
                    ],

                    expected_points=
                    question[
                        "expected_points"
                    ],

                    max_score=
                    question[
                        "marks"
                    ]
                )
            )

            total_score += (
                evaluation["score"]
            )

            total_max_score += (
                evaluation["max_score"]
            )

            results.append(
                {
                    "question_id":
                    question_id,

                    "question_text":
                    question[
                        "question_text"
                    ],

                    "score":
                    evaluation[
                        "score"
                    ],

                    "max_score":
                    evaluation[
                        "max_score"
                    ],

                    "semantic_similarity":
                    evaluation[
                        "semantic_similarity"
                    ],

                    "rubric_coverage":
                    evaluation[
                        "rubric_coverage"
                    ],

                    "feedback":
                    evaluation[
                        "feedback"
                    ],

                    "matched_points":
                    evaluation[
                        "matched_points"
                    ],

                    "missing_points":
                    evaluation[
                        "missing_points"
                    ]
                }
            )

        percentage = 0.0

        if total_max_score > 0:

            percentage = round(
                (
                    total_score
                    /
                    total_max_score
                ) * 100,
                2
            )

        return {

            "assessment_id":
            assessment_id,

            "total_questions":
            len(results),

            "total_score":
            total_score,

            "max_score":
            total_max_score,

            "percentage":
            percentage,

            "results":
            results
        }