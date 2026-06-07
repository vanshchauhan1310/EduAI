from pathlib import Path

from app.ai.exam_prep.assessment_generator import (
    AssessmentGenerator
)

from app.ai.exam_prep.assessment_store import (
    AssessmentStore
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

assessment_id = (
    AssessmentStore
    .save_assessment(
        assessment
    )
)

print(
    f"Saved: {assessment_id}"
)

loaded = (
    AssessmentStore
    .load_assessment(
        assessment_id
    )
)

print(
    f"Loaded: "
    f"{loaded['assessment_id']}"
)

print(
    "Exists:",
    AssessmentStore
    .assessment_exists(
        assessment_id
    )
)

print(
    "Count:",
    AssessmentStore
    .count_assessments()
)