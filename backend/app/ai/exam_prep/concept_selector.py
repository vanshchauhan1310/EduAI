import json
import random
from pathlib import Path
from typing import List, Dict


class ConceptSelector:

    def __init__(self, knowledge_base_path: Path):

        with open(
            knowledge_base_path,
            "r",
            encoding="utf-8"
        ) as f:

            self.data = json.load(f)

    def get_topics(self) -> List[str]:

        return [
            topic.strip()
            for topic in self.data.get(
                "topics",
                []
            )
            if isinstance(topic, str)
        ]

    def get_important_concepts(self) -> List[str]:

        concepts = []

        for item in self.data.get(
            "important_concepts",
            []
        ):

            if isinstance(item, str):

                concepts.append(
                    item.strip()
                )

            elif isinstance(item, dict):

                concept = (
                    item.get("concept")
                    or item.get("name")
                    or item.get("title")
                )

                if concept:
                    concepts.append(
                        concept.strip()
                    )

        return concepts

    def get_definition_map(self) -> Dict:

        definitions = {}

        for item in self.data.get(
            "definitions",
            []
        ):

            if isinstance(item, dict):

                term = (
                    item.get("term")
                    or item.get("concept")
                    or item.get("name")
                )

                definition = (
                    item.get("definition")
                    or item.get("description")
                )

                if term and definition:

                    definitions[
                        term.strip()
                    ] = definition.strip()

        return definitions

    def get_all_concepts(self) -> List[str]:

        concepts = []

        concepts.extend(
            self.get_topics()
        )

        concepts.extend(
            self.get_important_concepts()
        )

        unique = []

        seen = set()

        for concept in concepts:

            if (
                concept
                and concept not in seen
            ):

                seen.add(concept)

                unique.append(concept)

        return unique

    def random_concept(self) -> str:

        concepts = (
            self.get_all_concepts()
        )

        if not concepts:

            raise ValueError(
                "No concepts found."
            )

        return random.choice(
            concepts
        )

    def random_concepts(
        self,
        count: int
    ) -> List[str]:

        concepts = (
            self.get_all_concepts()
        )

        if not concepts:

            return []

        if count >= len(concepts):

            random.shuffle(
                concepts
            )

            return concepts

        return random.sample(
            concepts,
            count
        )

    def concepts_by_difficulty(
        self,
        difficulty: str
    ) -> List[str]:

        concepts = (
            self.get_all_concepts()
        )

        if difficulty == "easy":

            return concepts[:10]

        elif difficulty == "medium":

            return concepts[5:]

        elif difficulty == "hard":

            return concepts

        return concepts