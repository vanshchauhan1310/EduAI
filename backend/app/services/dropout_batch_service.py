import pandas as pd
import tempfile

from pathlib import Path
from fastapi.responses import FileResponse

from app.ai.dropout.predict import (
    predict_dropout
)

from app.ai.dropout.risk_detector import (
    get_risk_level
)

from app.ai.dropout.recommendation_engine import (
    get_recommendation
)

BASE_DIR = Path(__file__).resolve().parents[2]


async def process_excel(file):

    temp_input = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".xlsx"
    )

    contents = await file.read()

    temp_input.write(contents)

    temp_input.close()

    df = pd.read_excel(
        temp_input.name
    )

    probabilities = []
    risk_levels = []
    recommendations = []

    for _, row in df.iterrows():

        student = row.to_dict()

        probability = predict_dropout(
            student
        )

        score, level = get_risk_level(
            probability
        )

        recommendation = get_recommendation(
            level
        )

        probabilities.append(score)
        risk_levels.append(level)
        recommendations.append(
            recommendation
        )

    df["dropout_probability"] = probabilities
    df["risk_level"] = risk_levels
    df["recommendation"] = recommendations

    output_dir = BASE_DIR / "outputs"

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        output_dir /
        "dropout_predictions.xlsx"
    )

    df.to_excel(
        output_file,
        index=False
    )

    return FileResponse(
        path=str(output_file),
        filename="dropout_predictions.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )