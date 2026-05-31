import joblib
import pandas as pd

model = joblib.load(
    "app/ai/dropout/model.pkl"
)

feature_columns = joblib.load(
    "app/ai/dropout/feature_columns.pkl"
)

def predict_dropout(student_data):

    df = pd.DataFrame([student_data])

    df = df.reindex(
        columns=feature_columns,
        fill_value=0
    )

    probability = model.predict_proba(df)[0][1]

    return float(probability)