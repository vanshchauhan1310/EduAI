import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[3]

PYQ_DB = (
    BASE_DIR
    / "data"
    / "pyq_database"
    / "jesc101_pyq.json"
)


class QuestionLoader:

    @staticmethod
    def load_database():

        with open(
            PYQ_DB,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    @staticmethod
    def get_question_by_id(
        question_id: str
    ):

        data = QuestionLoader.load_database()

        questions = data.get(
            "questions",
            []
        )

        for question in questions:

            if (
                question["question_id"]
                == question_id
            ):
                return question

        return None

    @staticmethod
    def get_question_by_number(
        question_number: str
    ):

        data = QuestionLoader.load_database()

        questions = data.get(
            "questions",
            []
        )

        for question in questions:

            if (
                question["question_number"]
                == question_number
            ):
                return question

        return None