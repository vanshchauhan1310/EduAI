import json
import random
import uuid

from pathlib import Path

from app.ai.exam_prep.concept_selector import (
    ConceptSelector
)

from app.ai.exam_prep.context_builder import (
    ContextBuilder
)

from app.ai.exam_prep.question_generator import (
    QuestionGenerator
)


class AssessmentGenerator:

    def __init__(self):

        self.generator = (
            QuestionGenerator()
        )

    def generate_assessment(
        self,
        chapter_id: str,
        knowledge_base_path: Path,
        pyq_database_path: Path,
        pattern_library_path: Path,
        difficulty: str,
        num_questions: int
    ):

        selector = ConceptSelector(
            knowledge_base_path
        )

        context_builder = (
            ContextBuilder(
                knowledge_base_path,
                pyq_database_path
            )
        )

        with open(
            pattern_library_path,
            "r",
            encoding="utf-8"
        ) as f:

            pattern_library = (
                json.load(f)
            )

        concepts = (
            selector.random_concepts(
                num_questions
            )
        )

        pattern_names = list(
            pattern_library[
                "patterns"
            ].keys()
        )

        questions = []

        for concept in concepts:

            pattern = random.choice(
                pattern_names
            )

            pattern_info = (
                pattern_library[
                    "patterns"
                ][pattern]
            )

            marks = random.choice(
                pattern_info["marks"]
            )

            context = (
                context_builder
                .get_concept_context(
                    concept
                )
            )

            question = (
                self.generator
                .generate_question(
                    context=context,
                    pattern=pattern,
                    difficulty=difficulty,
                    marks=marks
                )
            )

            questions.append(
                question
            )

        total_marks = sum(
            q["marks"]
            for q in questions
        )

        return {

            "assessment_id":
                str(uuid.uuid4()),

            "chapter_id":
                chapter_id,

            "difficulty":
                difficulty,

            "total_questions":
                len(questions),

            "total_marks":
                total_marks,

            "questions":
                questions
        }