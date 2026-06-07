import json
from pathlib import Path

from app.ai.exam_prep.assessment_generator import (
    AssessmentGenerator
)


def main():

    generator = AssessmentGenerator()

    assessment = generator.generate_assessment(
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

        num_questions=3
    )

    print(
        json.dumps(
            assessment,
            indent=4,
            ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()