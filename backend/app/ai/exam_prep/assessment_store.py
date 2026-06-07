# app/ai/exam_prep/assessment_store.py

import json

from pathlib import Path
from typing import Dict, Optional, List


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[3]
)

ASSESSMENT_DIR = (
    BASE_DIR
    / "data"
    / "generated_assessments"
)

ASSESSMENT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


class AssessmentStore:

    @staticmethod
    def _get_file_path(
        assessment_id: str
    ) -> Path:

        return (
            ASSESSMENT_DIR
            / f"{assessment_id}.json"
        )

    @classmethod
    def save_assessment(
        cls,
        assessment: Dict
    ) -> str:

        assessment_id = (
            assessment.get(
                "assessment_id"
            )
        )

        if not assessment_id:

            raise ValueError(
                "assessment_id is missing"
            )

        file_path = (
            cls._get_file_path(
                assessment_id
            )
        )

        try:

            with open(
                file_path,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    assessment,
                    f,
                    indent=4,
                    ensure_ascii=False
                )

        except Exception as e:

            raise IOError(
                f"Failed to save assessment "
                f"{assessment_id}"
            ) from e

        return assessment_id

    @classmethod
    def load_assessment(
        cls,
        assessment_id: str
    ) -> Optional[Dict]:

        file_path = (
            cls._get_file_path(
                assessment_id
            )
        )

        if not file_path.exists():

            return None

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as f:

                return json.load(f)

        except Exception as e:

            raise IOError(
                f"Failed to load assessment "
                f"{assessment_id}"
            ) from e

    @classmethod
    def delete_assessment(
        cls,
        assessment_id: str
    ) -> bool:

        file_path = (
            cls._get_file_path(
                assessment_id
            )
        )

        if not file_path.exists():

            return False

        try:

            file_path.unlink()

            return True

        except Exception as e:

            raise IOError(
                f"Failed to delete assessment "
                f"{assessment_id}"
            ) from e

    @classmethod
    def assessment_exists(
        cls,
        assessment_id: str
    ) -> bool:

        return (
            cls._get_file_path(
                assessment_id
            ).exists()
        )

    @classmethod
    def list_assessments(
        cls
    ) -> List[str]:

        assessments = []

        for file in (
            ASSESSMENT_DIR.glob(
                "*.json"
            )
        ):

            assessments.append(
                file.stem
            )

        return sorted(
            assessments
        )

    @classmethod
    def count_assessments(
        cls
    ) -> int:

        return len(
            cls.list_assessments()
        )