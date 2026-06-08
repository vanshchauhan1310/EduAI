import json
import requests

from typing import Dict

from app.core.config import settings


class LLMQuestionGenerator:
    """
    Generates exam questions via the NVIDIA NIM API (OpenAI-compatible
    chat completions). Requires NVIDIA_NIM_API_KEY to be set in .env —
    get a free key at https://build.nvidia.com/
    """

    def __init__(
        self,
        model_name: str | None = None
    ):

        if not settings.NVIDIA_NIM_API_KEY:
            raise RuntimeError(
                "NVIDIA_NIM_API_KEY is not configured in backend/.env. "
                "Get a free key at: https://build.nvidia.com/"
            )

        self.model_name = model_name or settings.NVIDIA_NIM_MODEL

        self.base_url = (
            f"{settings.NVIDIA_NIM_BASE_URL.rstrip('/')}/chat/completions"
        )

        self.headers = {
            "Authorization": f"Bearer {settings.NVIDIA_NIM_API_KEY}",
            "Content-Type": "application/json",
        }

    def build_prompt(
        self,
        context: Dict,
        difficulty: str,
        marks: int
    ) -> str:

        return f"""
You are an expert CBSE Class 10 Science examiner.

Generate ONE NEW question.

Return ONLY valid JSON.

Format:

{{
    "question_text": "",
    "sample_answer": "",
    "expected_points": [
        ""
    ]
}}

IMPORTANT RULES:

1. Output ONLY JSON.
2. No markdown.
3. No ```json blocks.
4. No explanation.
5. expected_points MUST be a list of strings.
6. sample_answer must directly answer the question.
7. Generate a NEW CBSE-style question.
8. Difficulty = {difficulty}
9. Marks = {marks}

CORRECT:

{{
    "question_text": "What is corrosion?",
    "sample_answer": "Corrosion is the gradual deterioration of metals due to chemical reactions with the environment.",
    "expected_points": [
        "Definition of corrosion",
        "Chemical reaction with environment",
        "Deterioration of metal"
    ]
}}

WRONG:

{{
    "question_text": "...",
    "sample_answer": "...",
    "expected_points": [1,2,3]
}}

Concept:
{context["concept"]}

Topics:
{json.dumps(context.get("topics", []), indent=2)}

Definitions:
{json.dumps(context.get("definitions", []), indent=2)}

Important Concepts:
{json.dumps(context.get("important_concepts", []), indent=2)}

Common Mistakes:
{json.dumps(context.get("common_mistakes", []), indent=2)}

Related PYQs:
{json.dumps(context.get("related_pyqs", []), indent=2)}
"""

    def _clean_json_response(
        self,
        text: str
    ) -> str:

        text = text.strip()

        if text.startswith(
            "```json"
        ):
            text = text[7:]

        elif text.startswith(
            "```"
        ):
            text = text[3:]

        if text.endswith(
            "```"
        ):
            text = text[:-3]

        return text.strip()

    def _validate_response(
        self,
        result: Dict
    ):

        required_keys = [
            "question_text",
            "sample_answer",
            "expected_points"
        ]

        for key in required_keys:

            if key not in result:

                raise ValueError(
                    f"Missing key: {key}"
                )

        if not isinstance(
            result["expected_points"],
            list
        ):
            raise ValueError(
                "expected_points must be a list"
            )

        if len(
            result["expected_points"]
        ) == 0:
            raise ValueError(
                "expected_points is empty"
            )

        for point in result[
            "expected_points"
        ]:

            if not isinstance(
                point,
                str
            ):
                raise ValueError(
                    "expected_points must contain strings"
                )

    def generate_question(
        self,
        context: Dict,
        difficulty: str,
        marks: int
    ) -> Dict:

        prompt = self.build_prompt(
            context,
            difficulty,
            marks
        )

        response = requests.post(
            self.base_url,
            headers=self.headers,
            json={
                "model":
                    self.model_name,

                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                "temperature": 0.3,

                "max_tokens": 1024,

                "stream":
                    False
            },
            timeout=120
        )

        response.raise_for_status()

        raw = (
            response
            .json()["choices"][0]["message"]
            .get(
                "content",
                ""
            )
        )

        raw = self._clean_json_response(
            raw
        )

        try:

            result = json.loads(
                raw
            )

        except Exception as e:

            raise ValueError(
                f"\nJSON Parse Failed\n\n"
                f"Raw Response:\n{raw}"
            ) from e

        self._validate_response(
            result
        )

        return {
            "question_text":
                result[
                    "question_text"
                ],

            "sample_answer":
                result[
                    "sample_answer"
                ],

            "expected_points":
                result[
                    "expected_points"
                ]
        }