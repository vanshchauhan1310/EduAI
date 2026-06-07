import joblib
import pandas as pd

from functools import lru_cache


@lru_cache(maxsize=1)
def get_model():
    return joblib.load(
        "app/ai/dropout/model.pkl"
    )


@lru_cache(maxsize=1)
def get_feature_columns():
    return joblib.load(
        "app/ai/dropout/feature_columns.pkl"
    )


def predict_dropout(student_data):

    model = get_model()
    feature_columns = get_feature_columns()

    df = pd.DataFrame([student_data])

    df = df.reindex(
        columns=feature_columns,
        fill_value=0
    )

    probability = model.predict_proba(df)[0][1]

    return float(probability)