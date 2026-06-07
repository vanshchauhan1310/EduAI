import json
from pathlib import Path
from typing import Dict, List


class ContextBuilder:

    def __init__(
        self,
        knowledge_base_path: Path,
        pyq_database_path: Path
    ):

        with open(
            knowledge_base_path,
            "r",
            encoding="utf-8"
        ) as f:

            self.knowledge_base = json.load(f)

        with open(
            pyq_database_path,
            "r",
            encoding="utf-8"
        ) as f:

            self.pyq_database = json.load(f)

    def get_concept_context(
        self,
        concept: str,
        max_pyqs: int = 5
    ) -> Dict:

        context = {

            "concept": concept,

            "topics": [],

            "definitions": [],

            "important_concepts": [],

            "common_mistakes": [],

            "related_pyqs": []
        }

        # Topics
        for topic in self.knowledge_base.get(
            "topics",
            []
        ):

            if (
                concept.lower()
                in str(topic).lower()
            ):

                context["topics"].append(
                    topic
                )

        # Definitions
        for definition in self.knowledge_base.get(
            "definitions",
            []
        ):

            if (
                concept.lower()
                in str(definition).lower()
            ):

                context["definitions"].append(
                    definition
                )

        # Important concepts
        for item in self.knowledge_base.get(
            "important_concepts",
            []
        ):

            if (
                concept.lower()
                in str(item).lower()
            ):

                context[
                    "important_concepts"
                ].append(item)

        # Common mistakes
        for item in self.knowledge_base.get(
            "common_mistakes",
            []
        ):

            if (
                concept.lower()
                in str(item).lower()
            ):

                context[
                    "common_mistakes"
                ].append(item)

        # Related PYQs
        for question in self.pyq_database.get(
            "questions",
            []
        ):

            if (
                concept.lower()
                in question[
                    "question_text"
                ].lower()
            ):

                context[
                    "related_pyqs"
                ].append(
                    {
                        "question":
                        question[
                            "question_text"
                        ],

                        "difficulty":
                        question[
                            "difficulty"
                        ],

                        "marks":
                        question[
                            "marks"
                        ],

                        "pattern":
                        question[
                            "pattern"
                        ]
                    }
                )

        context[
            "related_pyqs"
        ] = context[
            "related_pyqs"
        ][:max_pyqs]

        return context