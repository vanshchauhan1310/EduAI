from pathlib import Path

from app.ai.exam_prep.assessment_generator import (
    AssessmentGenerator
)

from app.ai.exam_prep.answer_evaluator import (
    AnswerEvaluator
)


generator = AssessmentGenerator()

assessment = (
    generator.generate_assessment(
        chapter_id="jesc101",

        knowledge_base_path=Path(
            "data/knowledge_base/jesc101.json"
        ),

        pyq_database_path=Path(
            "data/pyq_database/jesc101_pyq.json"
        ),

        pattern_library_path=Path(
            "data/pattern_library/jesc101_patterns.json"
        ),

        difficulty="medium",

        num_questions=1
    )
)

question = (
    assessment["questions"][0]
)

evaluator = (
    AnswerEvaluator()
)

result = (
    evaluator.evaluate(
        student_answer=
        question["sample_answer"],

        sample_answer=
        question["sample_answer"],

        expected_points=
        question["expected_points"],

        max_score=
        question["marks"]
    )
)

print(result)