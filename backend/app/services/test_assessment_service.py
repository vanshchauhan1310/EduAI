from app.services.assessment_service import (
    AssessmentService
)


def main():

    service = AssessmentService()

    print("\nGenerating Assessment...\n")

    assessment = (
        service.generate_assessment(
            chapter_id="jesc101",
            difficulty="medium",
            num_questions=2
        )
    )

    assessment_id = (
        assessment["assessment_id"]
    )

    print(
        f"Assessment ID: "
        f"{assessment_id}"
    )

    print("\nGenerated Questions:")
    print("=" * 80)

    answers = []

    for index, question in enumerate(
        assessment["questions"],
        start=1
    ):

        print(
            f"\nQuestion {index}"
        )

        print(
            f"Marks: "
            f"{question['marks']}"
        )

        print(
            question[
                "question_text"
            ]
        )

        print()

        student_answer = input(
            "Your Answer:\n> "
        )

        answers.append(
            {
                "question_id":
                question[
                    "question_id"
                ],

                "answer":
                student_answer
            }
        )

    print(
        "\nSubmitting Assessment..."
    )

    result = (
        service.submit_assessment(
            assessment_id=
            assessment_id,

            answers=
            answers
        )
    )

    print("\n")
    print("=" * 80)
    print("FINAL RESULT")
    print("=" * 80)

    print(
        f"Score: "
        f"{result['total_score']}"
        f"/{result['max_score']}"
    )

    print(
        f"Percentage: "
        f"{result['percentage']}%"
    )

    print("\nDetailed Results")
    print("=" * 80)

    for item in result[
        "results"
    ]:

        print(
            f"\nQuestion ID: "
            f"{item['question_id']}"
        )

        print(
            f"Score: "
            f"{item['score']}"
            f"/{item['max_score']}"
        )

        print(
            f"Semantic Similarity: "
            f"{item['semantic_similarity']}"
        )

        print(
            f"Rubric Coverage: "
            f"{item['rubric_coverage']}"
        )

        print("\nFeedback:")

        print(
            item["feedback"]
        )

        print("\nMatched Points:")

        for point in item[
            "matched_points"
        ]:

            print(
                f"✓ {point}"
            )

        print(
            "\nMissing Points:"
        )

        for point in item[
            "missing_points"
        ]:

            print(
                f"✗ {point}"
            )

        print(
            "\n" + "-" * 80
        )


if __name__ == "__main__":
    main()