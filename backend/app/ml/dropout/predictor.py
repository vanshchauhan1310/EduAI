"""
Dropout Predictor — Loads the trained XGBoost model and generates predictions.

Provides both single-student and batch-prediction interfaces.
Risk classification and recommendation generation are included here
for a single entry point.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ─── Model Paths ───────────────────────────────────────────────
_MODEL_DIR = Path(__file__).resolve().parent
_MODEL_PATH = _MODEL_DIR / "model.pkl"
_THRESHOLD_PATH = _MODEL_DIR / "threshold.pkl"
_FEATURE_COLUMNS_PATH = _MODEL_DIR / "feature_columns.pkl"


# ─── Lazy-loaded artifacts ─────────────────────────────────────
_model = None
_threshold: float = 0.40
_feature_columns: list[str] = []


def _load_artifacts() -> None:
    """Load model, threshold, and feature columns from disk (once)."""
    global _model, _threshold, _feature_columns

    if _model is not None:
        return  # already loaded

    logger.info("Loading dropout prediction model from %s", _MODEL_PATH)

    if not _MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model file not found: {_MODEL_PATH}. "
            "Run training first via POST /api/v1/dropout/run-training"
        )

    _model = joblib.load(_MODEL_PATH)

    if _THRESHOLD_PATH.exists():
        _threshold = float(joblib.load(_THRESHOLD_PATH))
    else:
        _threshold = 0.40
        logger.warning(
            "Threshold file not found. Using default: %.2f", _threshold
        )

    if _FEATURE_COLUMNS_PATH.exists():
        _feature_columns = joblib.load(_FEATURE_COLUMNS_PATH)
    else:
        _feature_columns = []
        logger.warning("Feature columns file not found.")

    logger.info(
        "Model loaded successfully. Threshold=%.2f, Features=%d",
        _threshold,
        len(_feature_columns),
    )


def reload_model() -> None:
    """Force-reload the model from disk (useful after retraining)."""
    global _model
    _model = None
    _load_artifacts()


# ─── Risk Classification ──────────────────────────────────────

def classify_risk(probability: float) -> tuple[float, str]:
    """
    Convert raw probability to a percentage score and risk level.

    Returns
    -------
    (score, level) where score is 0-100 and level is Low/Medium/High/Critical
    """
    score = round(probability * 100, 2)

    if score < 30:
        level = "Low"
    elif score < 60:
        level = "Medium"
    elif score < 80:
        level = "High"
    else:
        level = "Critical"

    return score, level


def get_recommendation(level: str) -> str:
    """Map risk level to a recommended intervention."""
    mapping = {
        "Low": "Continue regular monitoring",
        "Medium": "Schedule counselling and monitor attendance closely",
        "High": "Immediate intervention required. Contact guardian and create retention plan",
        "Critical": "Urgent escalation to HM/DEO. Deploy multi-stakeholder intervention within 48 hours",
    }
    return mapping.get(level, "Continue monitoring")


# ─── Prediction ────────────────────────────────────────────────

def predict_single(student_features: dict[str, Any]) -> dict[str, Any]:
    """
    Predict dropout risk for a single student.

    Parameters
    ----------
    student_features : dict
        Feature dictionary matching the model's expected columns.

    Returns
    -------
    dict with keys: dropout_probability, risk_level, recommendation
    """
    _load_artifacts()

    df = pd.DataFrame([student_features])

    # Ensure correct column order
    if _feature_columns:
        df = df.reindex(columns=_feature_columns, fill_value=0)

    probability = float(_model.predict_proba(df)[0][1])
    score, level = classify_risk(probability)
    recommendation = get_recommendation(level)

    return {
        "dropout_probability": score,
        "risk_level": level,
        "recommendation": recommendation,
    }


def predict_batch(features_df: pd.DataFrame) -> pd.DataFrame:
    """
    Predict dropout risk for a batch of students.

    Parameters
    ----------
    features_df : pd.DataFrame
        DataFrame with model-compatible feature columns.

    Returns
    -------
    pd.DataFrame
        Input DataFrame with added columns:
        dropout_probability, risk_level, recommendation
    """
    _load_artifacts()

    df = features_df.copy()

    # Ensure correct column order
    if _feature_columns:
        df = df.reindex(columns=_feature_columns, fill_value=0)

    # Get probabilities for the positive class (dropout)
    probabilities = _model.predict_proba(df)[:, 1]

    results = [classify_risk(float(p)) for p in probabilities]
    scores = [r[0] for r in results]
    levels = [r[1] for r in results]
    recommendations = [get_recommendation(lv) for lv in levels]

    output = features_df.copy()
    output["dropout_probability"] = scores
    output["risk_level"] = levels
    output["recommendation"] = recommendations

    logger.info(
        "Batch prediction complete: %d students processed, "
        "High/Critical=%d",
        len(output),
        sum(1 for lv in levels if lv in ("High", "Critical")),
    )

    return output