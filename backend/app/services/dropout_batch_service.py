import os
import tempfile
import pandas as pd

from pathlib import Path

from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from app.ai.dropout.predict import predict_dropout

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
    predictions = []

    for _, row in df.iterrows():

        student = row.to_dict()

        probability = predict_dropout(
            student
        )

        score, level = get_risk_level(
            probability
        )

        recommendation_list = get_recommendation(
            student,
            level
        )

        predicted_dropout = (
            "Yes"
            if level == "High"
            else "No"
        )

        probabilities.append(score)

        risk_levels.append(level)

        recommendations.append(
            " | ".join(recommendation_list)
        )

        predictions.append(
            predicted_dropout
        )

    df["dropout_probability"] = probabilities
    df["risk_level"] = risk_levels
    df["predicted_dropout"] = predictions
    df["recommendation"] = recommendations

    temp_output = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".xlsx"
    )

    output_file = temp_output.name

    temp_output.close()

    df.to_excel(
        output_file,
        index=False
    )

    if os.path.exists(
        temp_input.name
    ):
        os.remove(
            temp_input.name
        )

    return FileResponse(
        path=output_file,
        filename="dropout_predictions.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        background=BackgroundTask(
            os.remove,
            output_file
        )
    )