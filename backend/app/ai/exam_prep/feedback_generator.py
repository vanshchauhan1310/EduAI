# app/ai/exam_prep/feedback_generator.py

from typing import List


class FeedbackGenerator:

    @staticmethod
    def generate(
        matched_points: List[str],
        missing_points: List[str]
    ) -> str:

        feedback = []

        if matched_points:

            feedback.append(
                f"You covered {len(matched_points)} key concepts correctly."
            )

        if missing_points:

            feedback.append(
                "You should also include:"
            )

            for point in missing_points:
                feedback.append(f"- {point}")

        if not missing_points:

            feedback.append(
                "Excellent answer. All key points are covered."
            )

        return "\n".join(feedback)