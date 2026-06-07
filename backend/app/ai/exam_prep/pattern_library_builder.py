from pathlib import Path
from collections import defaultdict
import json

from app.ai.exam_prep.pattern_extractor import (
    PatternExtractor
)


class PatternLibraryBuilder:

    def build_from_file(
        self,
        pyq_json_path: Path
    ):

        with open(
            pyq_json_path,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        chapter_id = data["chapter_id"]

        pattern_stats = defaultdict(
            lambda: {
                "frequency": 0,
                "marks": set(),
                "answer_structures": set()
            }
        )

        for question in data["questions"]:

            extracted = (
                PatternExtractor.extract(
                    question
                )
            )

            pattern_name = extracted["pattern"]

            pattern_stats[
                pattern_name
            ]["frequency"] += 1

            pattern_stats[
                pattern_name
            ]["marks"].add(
                extracted["marks"]
            )

            pattern_stats[
                pattern_name
            ]["answer_structures"].add(
                tuple(
                    extracted[
                        "answer_structure"
                    ]
                )
            )

        final_patterns = {}

        for pattern, stats in pattern_stats.items():

            final_patterns[pattern] = {

                "frequency":
                stats["frequency"],

                "marks":
                sorted(
                    list(
                        stats["marks"]
                    )
                ),

                "answer_structures":
                [
                    list(x)
                    for x in stats[
                        "answer_structures"
                    ]
                ]
            }

        return {

            "chapter_id":
            chapter_id,

            "patterns":
            final_patterns
        }

    def save_pattern_library(
        self,
        pyq_json_path: Path,
        output_dir: Path
    ):

        library = self.build_from_file(
            pyq_json_path
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        output_path = (
            output_dir /
            f"{library['chapter_id']}_patterns.json"
        )

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                library,
                f,
                indent=4,
                ensure_ascii=False
            )

        return output_path