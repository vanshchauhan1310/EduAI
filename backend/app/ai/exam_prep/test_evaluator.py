# app/ai/exam_prep/test_evaluator.py

import json

from app.ai.exam_prep.answer_evaluator import AnswerEvaluator


PYQ_FILE = "data/pyq_database/jesc101_pyq.json"


def load_question(index: int = 0):

    with open(
        PYQ_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    questions = data.get("questions", [])

    if not questions:
        raise ValueError(
            "No questions found in PYQ database."
        )

    if index >= len(questions):
        raise IndexError(
            f"Question index {index} out of range."
        )

    return questions[index]


def print_question(question):

    print("\n" + "=" * 80)

    print(
        f"Question No : {question['question_number']}"
    )

    print(
        f"Difficulty  : {question['difficulty']}"
    )

    print(
        f"Marks       : {question['marks']}"
    )

    print("\nQUESTION:")
    print(question["question_text"])

    print("\nEXPECTED POINTS:")

    for idx, point in enumerate(
        question["expected_points"],
        start=1
    ):
        print(f"{idx}. {point}")

    print("=" * 80)


def main():

    question_index = int(
        input(
            "Enter question index (0-41): "
        )
    )

    question = load_question(
        question_index
    )

    print_question(question)

    print(
        "\nEnter Student Answer:"
    )

    student_answer = input(
        "\n> "
    )

    evaluator = AnswerEvaluator()

    result = evaluator.evaluate(
        student_answer=student_answer,
        sample_answer=question[
            "sample_answer"
        ],
        expected_points=question[
            "expected_points"
        ],
        max_score=question["marks"]
    )

    print("\nRESULT")
    print("=" * 80)

    print(
        f"Score: {result['score']}"
        f"/{result['max_score']}"
    )

    print(
        f"Semantic Similarity: "
        f"{result['semantic_similarity']}"
    )

    print(
        f"Rubric Coverage: "
        f"{result['rubric_coverage']}"
    )

    print("\nMatched Points:")

    for point in result[
        "matched_points"
    ]:
        print(f"✓ {point}")

    print("\nMissing Points:")

    for point in result[
        "missing_points"
    ]:
        print(f"✗ {point}")

    print("\nFeedback:")
    print(
        result["feedback"]
    )

    print("=" * 80)


if __name__ == "__main__":
    main()