def get_recommendation(student, level):

    recommendations = []

    if student.get("attendance_pct", 100) < 75:
        recommendations.append(
            "Discuss attendance issues with parents and monitor weekly."
        )

    if student.get("avg_marks", 100) < 50:
        recommendations.append(
            "Arrange academic support and tutoring."
        )

    if student.get("previous_failures", 0) >= 2:
        recommendations.append(
            "Create a subject-wise improvement plan."
        )

    if student.get("study_hours_per_day", 5) < 2:
        recommendations.append(
            "Increase daily study time with a structured schedule."
        )

    if student.get("teacher_feedback_score", 100) < 40:
        recommendations.append(
            "Schedule a parent-teacher meeting."
        )

    if student.get("disciplinary_incidents", 0) > 2:
        recommendations.append(
            "Provide behavioural counselling."
        )

    if not recommendations:

        if level == "Low":
            recommendations.append(
                "Continue regular monitoring."
            )

        elif level == "Medium":
            recommendations.append(
                "Monitor progress and provide guidance."
            )

        else:
            recommendations.append(
                "Immediate intervention recommended."
            )

    return recommendations