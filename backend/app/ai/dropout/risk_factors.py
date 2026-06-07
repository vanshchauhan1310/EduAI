def get_risk_factors(student):

    factors = []

    if student.get("attendance_pct", 100) < 75:
        factors.append(
            "Low attendance"
        )

    if student.get("avg_marks", 100) < 50:
        factors.append(
            "Poor academic performance"
        )

    if student.get("previous_failures", 0) >= 2:
        factors.append(
            "Multiple previous failures"
        )

    if student.get("study_hours_per_day", 5) < 2:
        factors.append(
            "Low study time"
        )

    if student.get("teacher_feedback_score", 100) < 40:
        factors.append(
            "Negative teacher feedback"
        )

    if student.get("disciplinary_incidents", 0) > 2:
        factors.append(
            "Behavioural concerns"
        )

    return factors[:3]