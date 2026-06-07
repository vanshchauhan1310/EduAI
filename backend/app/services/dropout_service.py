from app.ai.dropout.predict import (
    predict_dropout
)

from app.ai.dropout.risk_detector import (
    get_risk_level
)

from app.ai.dropout.recommendation_engine import (
    get_recommendation
)

from app.ai.dropout.risk_factors import (
    get_risk_factors
)


def predict_student_risk(student):

    probability = predict_dropout(
        student
    )

    score, level = get_risk_level(
        probability
    )

    recommendations = get_recommendation(
        student,
        level
    )

    risk_factors = get_risk_factors(
        student
    )

    return {
        "dropout_probability": score,
        "risk_level": level,
        "top_risk_factors": risk_factors,
        "recommendations": recommendations
    }