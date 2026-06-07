import re
from typing import List


class ExpectedPointsExtractor:

    @staticmethod
    def extract(sample_answer: str) -> List[str]:

        if not sample_answer:
            return []

        rubric_section = re.search(
            r"Award marks if answer contains:(.*?)(?:Chemical Equation|EASY|MEDIUM|HARD|$)",
            sample_answer,
            flags=re.IGNORECASE | re.DOTALL
        )

        if rubric_section:

            rubric_text = rubric_section.group(1)

            points = re.findall(
                r"N\s+(.*?)(?=\nN|\Z)",
                rubric_text,
                flags=re.DOTALL
            )

            cleaned_points = []

            for point in points:

                point = " ".join(point.split())

                if point:
                    cleaned_points.append(point)

            return cleaned_points

        # fallback

        sentences = re.split(
            r"\.|\n",
            sample_answer
        )

        return [
            s.strip()
            for s in sentences
            if s.strip()
        ]