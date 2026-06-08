import json
import random
import uuid

from concurrent.futures import ThreadPoolExecutor
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

# Default pattern library used when no pattern_library file exists
DEFAULT_PATTERNS = {
    "patterns": {
        "explain": {"marks": [2, 3, 5]},
        "define": {"marks": [1, 2]},
        "compare": {"marks": [3, 5]},
        "list": {"marks": [2, 3]},
        "short_answer": {"marks": [2, 3]},
        "long_answer": {"marks": [5]},
    }
}


class AssessmentGenerator:

    def __init__(self):

        self.generator = (
            QuestionGenerator()
        )

    def generate_assessment(
        self,
        chapter_id: str,
        knowledge_base_path: Path,
        pyq_database_path: Path = None,
        pattern_library_path: Path = None,
        difficulty: str = "MEDIUM",
        num_questions: int = 5
    ):

        selector = ConceptSelector(
            knowledge_base_path
        )

        context_builder = (
            ContextBuilder(
                knowledge_base_path,
                pyq_database_path  # None is handled safely now
            )
        )

        # Load pattern library if available, else use defaults
        if (
            pattern_library_path
            and Path(pattern_library_path).exists()
        ):
            with open(
                pattern_library_path,
                "r",
                encoding="utf-8"
            ) as f:
                pattern_library = json.load(f)
        else:
            pattern_library = DEFAULT_PATTERNS

        # Repeat concepts if we need more questions than there are unique concepts
        all_concepts = selector.get_all_concepts()
        if not all_concepts:
            all_concepts = [chapter_id]

        if num_questions <= len(all_concepts):
            concepts = random.sample(all_concepts, num_questions)
        else:
            # Allow repeats by cycling through concepts
            concepts = [
                all_concepts[i % len(all_concepts)]
                for i in range(num_questions)
            ]
            random.shuffle(concepts)

        pattern_names = list(
            pattern_library[
                "patterns"
            ].keys()
        )

        # Build each question's (context, pattern, marks) up front — this
        # is pure local computation (no I/O), so it stays sequential.
        question_specs = []

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

            question_specs.append(
                (context, pattern, marks)
            )

        # Each question requires a separate LLM call (~5-10s). Running them
        # concurrently keeps total latency close to a single call instead of
        # num_questions * call_latency, which was blowing past client timeouts.
        with ThreadPoolExecutor(max_workers=min(len(question_specs), 5)) as pool:
            questions = list(
                pool.map(
                    lambda spec: self.generator.generate_question(
                        context=spec[0],
                        pattern=spec[1],
                        difficulty=difficulty,
                        marks=spec[2]
                    ),
                    question_specs
                )
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