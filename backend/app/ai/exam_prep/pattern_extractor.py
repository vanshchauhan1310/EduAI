from typing import Dict, List
import re


class PatternExtractor:

    PATTERN_RULES = {
        "definition": [
            r"^what is\b",
            r"^define\b"
        ],

        "reasoning": [
            r"^why\b"
        ],

        "identification": [
            r"^identify\b",
            r"^name\b"
        ],

        "comparison": [
            r"^differentiate\b",
            r"^compare\b"
        ],

        "explanation": [
            r"^explain\b"
        ],

        "equation": [
            r"write.*equation",
            r"balanced.*equation"
        ],

        "observation": [
            r"what is observed",
            r"what happens when"
        ],

        "verification": [
            r"verify"
        ],

        "case_based": [
            r"case study",
            r"a student",
            r"an experiment"
        ]
    }

    @classmethod
    def detect_pattern(cls, question: str) -> str:

        q = question.lower().strip()

        for pattern, regexes in cls.PATTERN_RULES.items():

            for regex in regexes:

                if re.search(regex, q):
                    return pattern

        return "general"

    @staticmethod
    def answer_structure(pattern: str) -> List[str]:

        structures = {

            "definition":
            ["definition"],

            "reasoning":
            ["cause", "effect"],

            "comparison":
            ["similarity", "difference"],

            "identification":
            ["identify", "reason"],

            "equation":
            ["equation"],

            "observation":
            ["observation", "equation"],

            "case_based":
            ["analysis", "conclusion"]
        }

        return structures.get(
            pattern,
            ["answer"]
        )

    @classmethod
    def extract(cls, question_record: Dict) -> Dict:

        pattern = cls.detect_pattern(
            question_record["question_text"]
        )

        return {
            "question_id":
            question_record["question_id"],

            "pattern":
            pattern,

            "answer_structure":
            cls.answer_structure(pattern),

            "marks":
            question_record["marks"],

            "difficulty":
            question_record["difficulty"]
        }