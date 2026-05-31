import pandas as pd
from sklearn.preprocessing import LabelEncoder

DATA_PATH = "data/student_dropout.csv"

FEATURES = [
    "Age",
    "Travel_Time",
    "Study_Time",
    "Number_of_Failures",
    "Number_of_Absences",
    "Grade_1",
    "Grade_2",
    "Final_Grade",
    "Internet_Access",
    "School_Support",
    "Family_Support",
    "Health_Status",
]

TARGET = "Dropped_Out"


def load_training_data():
    df = pd.read_csv(DATA_PATH)

    categorical_cols = [
        "Internet_Access",
        "School_Support",
        "Family_Support",
    ]

    encoders = {}

    for col in categorical_cols:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le

    X = df[FEATURES]
    y = df[TARGET]

    return X, y, encoders