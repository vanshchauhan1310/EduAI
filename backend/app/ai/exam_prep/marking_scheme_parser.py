from pathlib import Path
import fitz
import re
from typing import Dict, List


class MarkingSchemeParser:

    @staticmethod
    def extract_text(pdf_path: str) -> str:

        doc = fitz.open(pdf_path)

        pages = []

        for page in doc:
            text = page.get_text()

            if text:
                pages.append(text)

        doc.close()

        return "\n".join(pages)

    @staticmethod
    def extract_model_answer(block: str) -> str:

        model_match = re.search(
            r"Model Answer:(.*?)(?=Award marks if answer contains:|Chemical Equation\(s\):|EASY|MEDIUM|HARD|$)",
            block,
            flags=re.IGNORECASE | re.DOTALL
        )

        if not model_match:
            return ""

        answer = model_match.group(1)

        answer = " ".join(answer.split())

        return answer.strip()

    @staticmethod
    def extract_rubric_points(block: str) -> List[str]:

        rubric_match = re.search(
            r"Award marks if answer contains:(.*?)(?=Chemical Equation\(s\):|EASY|MEDIUM|HARD|$)",
            block,
            flags=re.IGNORECASE | re.DOTALL
        )

        if not rubric_match:
            return []

        rubric_text = rubric_match.group(1)

        points = re.findall(
            r"N\s+(.*?)(?=\nN|\Z)",
            rubric_text,
            flags=re.DOTALL
        )

        cleaned = []

        for point in points:

            point = " ".join(point.split())

            if point:
                cleaned.append(point)

        return cleaned

    @staticmethod
    def extract_equations(block: str) -> List[str]:

        equation_match = re.search(
            r"Chemical Equation\(s\):(.*?)(?=EASY|MEDIUM|HARD|$)",
            block,
            flags=re.IGNORECASE | re.DOTALL
        )

        if not equation_match:
            return []

        equation_text = equation_match.group(1)

        equations = [
            eq.strip()
            for eq in equation_text.split("|")
            if eq.strip()
        ]

        return equations

    @staticmethod
    def parse_marking_scheme(text: str) -> Dict:

        question_pattern = r"(Q\d+[\s\S]*?)(?=Q\d+|$)"

        blocks = re.findall(
            question_pattern,
            text,
            flags=re.IGNORECASE
        )

        parsed = {}

        for block in blocks:

            q_match = re.search(
                r"(Q\d+)",
                block,
                flags=re.IGNORECASE
            )

            if not q_match:
                continue

            question_no = q_match.group(1).upper()

            mark_match = re.search(
                r"(\d+)\s*Mark",
                block,
                flags=re.IGNORECASE
            )

            marks = (
                int(mark_match.group(1))
                if mark_match
                else 1
            )

            parsed[question_no] = {
                "marks": marks,
                "sample_answer":
                    MarkingSchemeParser.extract_model_answer(
                        block
                    ),

                "rubric_points":
                    MarkingSchemeParser.extract_rubric_points(
                        block
                    ),

                "chemical_equations":
                    MarkingSchemeParser.extract_equations(
                        block
                    )
            }

        return parsed

    def parse_pdf(self, pdf_path: str) -> Dict:

        text = self.extract_text(pdf_path)

        return self.parse_marking_scheme(text)