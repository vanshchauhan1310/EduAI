import json
from pathlib import Path
from datetime import datetime

import ollama

OLLAMA_MODEL = "llama3.2"

KNOWLEDGE_BASE_DIR = Path("data/knowledge_base")
KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)

MAX_CHUNK_SIZE = 5000


def chunk_text(text: str, chunk_size: int = MAX_CHUNK_SIZE):
    return [
        text[i:i + chunk_size]
        for i in range(0, len(text), chunk_size)
    ]


def call_ollama_json(prompt: str, retries: int = 3):

    last_error = None

    for attempt in range(retries):

        try:

            response = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                format="json",
                options={
                    "temperature": 0.1
                }
            )

            return json.loads(
                response["message"]["content"]
            )

        except Exception as e:
            last_error = e

    raise RuntimeError(
        f"Ollama failed after {retries} retries: {last_error}"
    )


def extract_topics(text_chunk: str):

    prompt = f"""
Extract the major topics discussed.

Return JSON only.

{{
  "topics": []
}}

Text:
{text_chunk}
"""

    return call_ollama_json(prompt).get(
        "topics",
        []
    )


def extract_definitions(text_chunk: str):

    prompt = f"""
Extract important exam-relevant definitions.

Return JSON only.

{{
  "definitions": [
    {{
      "term": "",
      "definition": ""
    }}
  ]
}}

Text:
{text_chunk}
"""

    return call_ollama_json(prompt).get(
        "definitions",
        []
    )


def extract_formulae(text_chunk: str):

    prompt = f"""
Extract important formulae, equations,
chemical equations, reactions, laws,
or relationships.

Return JSON only.

{{
  "formulae": [
    {{
      "name": "",
      "formula": "",
      "used_for": ""
    }}
  ]
}}

Text:
{text_chunk}
"""

    return call_ollama_json(prompt).get(
        "formulae",
        []
    )


def extract_concepts(text_chunk: str):

    prompt = f"""
Extract the most important concepts.

Return JSON only.

{{
  "important_concepts": []
}}

Text:
{text_chunk}
"""

    return call_ollama_json(prompt).get(
        "important_concepts",
        []
    )


def extract_common_mistakes(text_chunk: str):

    prompt = f"""
Based on this chapter,
identify common mistakes students make.

Return JSON only.

{{
  "common_mistakes": []
}}

Text:
{text_chunk}
"""

    return call_ollama_json(prompt).get(
        "common_mistakes",
        []
    )


def deduplicate_strings(items):

    seen = set()

    result = []

    for item in items:

        normalized = item.strip().lower()

        if normalized not in seen:

            seen.add(normalized)

            result.append(item)

    return result


def deduplicate_definitions(definitions):

    seen = set()

    result = []

    for item in definitions:

        term = item.get(
            "term",
            ""
        ).strip().lower()

        if term and term not in seen:

            seen.add(term)

            result.append(item)

    return result


def deduplicate_formulae(formulae):

    seen = set()

    result = []

    for item in formulae:

        formula = item.get(
            "formula",
            ""
        ).strip().lower()

        if formula and formula not in seen:

            seen.add(formula)

            result.append(item)

    return result


def estimate_difficulty(text_length):

    if text_length < 5000:
        return "easy"

    if text_length < 15000:
        return "medium"

    return "hard"


def estimate_study_time(text_length):

    if text_length < 5000:
        return 30

    if text_length < 15000:
        return 60

    return 90


def save_knowledge(knowledge: dict):

    chapter_id = (
        knowledge["chapter"]
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )

    output_file = (
        KNOWLEDGE_BASE_DIR /
        f"{chapter_id}.json"
    )

    with open(
            output_file,
            "w",
            encoding="utf-8"
    ) as f:

        json.dump(
            knowledge,
            f,
            indent=2,
            ensure_ascii=False
        )

    return output_file


def extract_chapter_knowledge(
        chapter_text: str,
        chapter_name: str,
        subject: str,
        source_pdf: str = ""
):

    print(
        f"[Knowledge] Processing: "
        f"{chapter_name}"
    )

    chunks = chunk_text(chapter_text)

    all_topics = []
    all_definitions = []
    all_formulae = []
    all_concepts = []
    all_mistakes = []

    for index, chunk in enumerate(chunks):

        print(
            f"[Knowledge] "
            f"Chunk {index + 1}/{len(chunks)}"
        )

        try:

            all_topics.extend(
                extract_topics(chunk)
            )

            all_definitions.extend(
                extract_definitions(chunk)
            )

            all_formulae.extend(
                extract_formulae(chunk)
            )

            all_concepts.extend(
                extract_concepts(chunk)
            )

            all_mistakes.extend(
                extract_common_mistakes(chunk)
            )

        except Exception as e:

            print(
                f"[Knowledge] "
                f"Chunk failed: {e}"
            )

    knowledge = {
        "chapter": chapter_name,
        "subject": subject,
        "source_pdf": source_pdf,
        "processed_at": (
            datetime.utcnow()
            .isoformat()
        ),
        "topics": deduplicate_strings(
            all_topics
        ),
        "definitions": (
            deduplicate_definitions(
                all_definitions
            )
        ),
        "formulae": (
            deduplicate_formulae(
                all_formulae
            )
        ),
        "important_concepts": (
            deduplicate_strings(
                all_concepts
            )
        ),
        "common_mistakes": (
            deduplicate_strings(
                all_mistakes
            )
        ),
        "difficulty_level": (
            estimate_difficulty(
                len(chapter_text)
            )
        ),
        "estimated_study_minutes": (
            estimate_study_time(
                len(chapter_text)
            )
        )
    }

    output_file = save_knowledge(
        knowledge
    )

    print(
        f"[Knowledge] Saved: "
        f"{output_file}"
    )

    return knowledge


def load_chapter_knowledge(
        chapter_id: str
):

    file_path = (
        KNOWLEDGE_BASE_DIR /
        f"{chapter_id}.json"
    )

    if not file_path.exists():

        raise FileNotFoundError(
            f"{chapter_id} not found"
        )

    with open(
            file_path,
            encoding="utf-8"
    ) as f:

        return json.load(f)


def list_available_chapters():

    chapters = []

    for file in (
            KNOWLEDGE_BASE_DIR
            .glob("*.json")
    ):

        try:

            with open(
                    file,
                    encoding="utf-8"
            ) as f:

                data = json.load(f)

            chapters.append(
                {
                    "chapter_id": file.stem,
                    "chapter_name": data.get(
                        "chapter"
                    ),
                    "subject": data.get(
                        "subject"
                    ),
                    "difficulty_level": (
                        data.get(
                            "difficulty_level"
                        )
                    ),
                    "estimated_study_minutes": (
                        data.get(
                            "estimated_study_minutes"
                        )
                    )
                }
            )

        except Exception:
            pass

    return sorted(
        chapters,
        key=lambda x: x["chapter_name"]
    )