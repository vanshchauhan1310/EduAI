from app.ai.dropout.predict import (
    predict_dropout
)

from app.ai.dropout.risk_detector import (
    risk_level
)

from app.ai.dropout.recommendation_engine import (
    recommendation
)

def predict_student_risk(student):

    probability = predict_dropout(
        student
    )

    score, level = risk_level(
        probability
    )

    action = recommendation(
        level
    )

    return {
        "dropout_probability": score,
        "risk_level": level,
        "recommended_action": action
    }