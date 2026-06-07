from pathlib import Path
from typing import Dict, List
import json
import uuid

from app.ai.exam_prep.pyq_parser import PYQParser
from app.ai.exam_prep.marking_scheme_parser import MarkingSchemeParser
from app.ai.exam_prep.pattern_extractor import PatternExtractor
from app.ai.exam_prep.expected_points_extractor import (
    ExpectedPointsExtractor
)


class PYQProcessor:

    def __init__(self):

        self.pyq_parser = PYQParser()
        self.marking_parser = MarkingSchemeParser()
        self.pattern_extractor = PatternExtractor()

    def process_chapter(
        self,
        chapter_id: str,
        pyq_folder: Path,
        marking_folder: Path,
        output_folder: Path
    ) -> Dict:

        pyq_files = sorted(pyq_folder.glob("*.pdf"))
        marking_files = sorted(marking_folder.glob("*.pdf"))

        if not pyq_files:
            raise FileNotFoundError(
                f"No PYQ PDFs found in {pyq_folder}"
            )

        if not marking_files:
            raise FileNotFoundError(
                f"No marking scheme PDFs found in {marking_folder}"
            )

        # Parse all marking schemes once
        marking_database = {}

        for marking_file in marking_files:

            parsed = self.marking_parser.parse_pdf(
                str(marking_file)
            )

            marking_database.update(parsed)

        questions = []

        for pyq_file in pyq_files:

            extracted_questions = self.process_pyq_file(
                chapter_id=chapter_id,
                pyq_pdf=pyq_file,
                marking_database=marking_database
            )

            questions.extend(extracted_questions)

        final_json = {
            "chapter_id": chapter_id,
            "total_questions": len(questions),
            "questions": questions
        }

        output_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        output_path = (
            output_folder /
            f"{chapter_id}_pyq.json"
        )

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                final_json,
                f,
                indent=4,
                ensure_ascii=False
            )

        return final_json

    def process_pyq_file(
        self,
        chapter_id: str,
        pyq_pdf: Path,
        marking_database: Dict
    ) -> List[Dict]:

        pyq_text = self.pyq_parser.extract_text(
            str(pyq_pdf)
        )

        extracted_questions = (
            self.pyq_parser.extract_questions(
                pyq_text
            )
        )

        results = []

        for index, question_data in enumerate(
            extracted_questions,
            start=1
        ):

            if isinstance(question_data, str):

                question_text = question_data
                question_number = f"Q{index}"

            else:

                question_text = question_data.get(
                    "question_text",
                    ""
                )

                question_number = question_data.get(
                    "question_number",
                    f"Q{index}"
                )

            marking_info = marking_database.get(
                question_number,
                {}
            )

            marks = marking_info.get(
                "marks",
                1
            )

            sample_answer = marking_info.get(
                "sample_answer",
                ""
            )

            difficulty = self.classify_difficulty(
                question_text,
                marks
            )

            expected_points = (
                ExpectedPointsExtractor.extract(
                    sample_answer
                )
            )

            pattern_data = (
                self.pattern_extractor.extract(
                    {
                        "question_id":
                        f"{chapter_id}_{index}",

                        "question_text":
                        question_text,

                        "marks":
                        marks,

                        "difficulty":
                        difficulty
                    }
                )
            )

            record = {

                "question_id":
                str(uuid.uuid4()),

                "chapter_id":
                chapter_id,

                "question_number":
                question_number,

                "question_text":
                question_text,

                "marks":
                marks,

                "difficulty":
                difficulty,

                "sample_answer":
                sample_answer,

                "expected_points":
                expected_points,

                "keywords":
                self.extract_keywords(
                    question_text
                ),

                "pattern":
                pattern_data["pattern"],

                "answer_structure":
                pattern_data[
                    "answer_structure"
                ]
            }

            results.append(record)

        return results

    def classify_difficulty(
        self,
        question: str,
        marks: int
    ) -> str:

        question = question.lower()

        if marks >= 5:
            return "hard"

        if any(
            word in question
            for word in [
                "analyse",
                "justify",
                "case study",
                "evaluate"
            ]
        ):
            return "hard"

        if marks >= 3:
            return "medium"

        return "easy"

    def extract_keywords(
        self,
        question: str
    ) -> List[str]:

        stopwords = {

            "what",
            "why",
            "is",
            "are",
            "the",
            "a",
            "an",
            "of",
            "to",
            "for",
            "with",
            "and",
            "in",
            "on",
            "by",
            "when",
            "how",
            "does",
            "do",
            "give",
            "write",
            "explain",
            "identify"
        }

        words = []

        for word in question.lower().split():

            word = (
                word.replace(",", "")
                .replace(".", "")
                .replace("?", "")
                .replace(":", "")
                .replace(";", "")
            )

            if (
                len(word) > 3
                and word not in stopwords
            ):
                words.append(word)

        return list(set(words))