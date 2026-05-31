import joblib
import pandas as pd

from pathlib import Path

from xgboost import XGBClassifier

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from sklearn.metrics import (
    roc_auc_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

BASE_DIR = Path(__file__).resolve().parents[3]

TRAIN_FILE = BASE_DIR / "data" / "train_students.csv"
TEST_FILE = BASE_DIR / "data" / "test_students.csv"

train_df = pd.read_csv(TRAIN_FILE)
test_df = pd.read_csv(TEST_FILE)

TARGET = "dropout_flag"

X_train = train_df.drop(
    columns=["student_id", TARGET]
)

y_train = train_df[TARGET]

X_test = test_df.drop(
    columns=["student_id", TARGET]
)

y_test = test_df[TARGET]

categorical_cols = X_train.select_dtypes(
    include=["object", "string"]
).columns.tolist()

preprocessor = ColumnTransformer(
    transformers=[
        (
            "cat",
            OneHotEncoder(
                handle_unknown="ignore"
            ),
            categorical_cols
        )
    ],
    remainder="passthrough"
)

dropouts = y_train.sum()
non_dropouts = len(y_train) - dropouts

scale_pos_weight = non_dropouts / dropouts

print(f"Dropouts: {dropouts}")
print(f"Non Dropouts: {non_dropouts}")
print(f"Scale Pos Weight: {scale_pos_weight:.2f}")

model = XGBClassifier(
    n_estimators=700,
    max_depth=5,
    learning_rate=0.03,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=scale_pos_weight,
    eval_metric="logloss",
    random_state=42
)

pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", model)
])

pipeline.fit(X_train, y_train)

probs = pipeline.predict_proba(X_test)[:, 1]

auc = roc_auc_score(y_test, probs)

print("\n" + "=" * 50)
print(f"ROC AUC: {auc:.4f}")
print("=" * 50)

DEPLOYMENT_THRESHOLD = 0.40

preds = (
    probs >= DEPLOYMENT_THRESHOLD
).astype(int)

accuracy = accuracy_score(
    y_test,
    preds
)

precision = precision_score(
    y_test,
    preds
)

recall = recall_score(
    y_test,
    preds
)

f1 = f1_score(
    y_test,
    preds
)

print("\nDeployment Threshold:", DEPLOYMENT_THRESHOLD)

print(f"Accuracy : {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall   : {recall:.4f}")
print(f"F1 Score : {f1:.4f}")

print("\nConfusion Matrix")

print(
    confusion_matrix(
        y_test,
        preds
    )
)

feature_names = pipeline.named_steps[
    "preprocessor"
].get_feature_names_out()

importances = pipeline.named_steps[
    "model"
].feature_importances_

importance_df = pd.DataFrame({
    "Feature": feature_names,
    "Importance": importances
})

importance_df = importance_df.sort_values(
    by="Importance",
    ascending=False
)

print("\nTop 15 Features\n")
print(
    importance_df.head(15)
)

importance_df.to_csv(
    BASE_DIR /
    "app" /
    "ai" /
    "dropout" /
    "feature_importance.csv",
    index=False
)

joblib.dump(
    pipeline,
    BASE_DIR /
    "app" /
    "ai" /
    "dropout" /
    "model.pkl"
)

joblib.dump(
    DEPLOYMENT_THRESHOLD,
    BASE_DIR /
    "app" /
    "ai" /
    "dropout" /
    "threshold.pkl"
)

joblib.dump(
    list(X_train.columns),
    BASE_DIR /
    "app" /
    "ai" /
    "dropout" /
    "feature_columns.pkl"
)

print("\nModel Saved Successfully")

def train():
    # move all your training code here
    print("Training Started")

    # training code...

    print("Training Complete")

if __name__ == "__main__":
    train()