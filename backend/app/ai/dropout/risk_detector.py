def get_risk_level(probability):

    score = round(
        probability * 100,
        2
    )

    if score < 30:
        level = "Low"

    elif score < 60:
        level = "Medium"

    else:
        level = "High"

    return score, level