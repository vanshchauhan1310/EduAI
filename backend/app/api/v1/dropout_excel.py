"""
FastAPI Router — Dropout Prediction Excel Upload & Template Download.

Endpoints:
    GET  /dropout/template       Download template Excel (columns = student_ml_input)
    POST /dropout/upload-predict Upload Excel → run predictions → return Excel
"""

from __future__ import annotations

import io
import logging
import uuid
from datetime import datetime
from typing import Any

import pandas as pd
import openpyxl
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.ml.dropout.predictor import predict_batch
from app.ml.dropout.feature_builder import MODEL_FEATURES
from app.services.dropout_prediction_service import DropoutPredictionService
from app.schemas.dropout_prediction import MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# ─── Constants ───────────────────────────────────────────────────

# Column names for the template (must match MODEL_FEATURES exactly)
TEMPLATE_COLUMNS = [
    "student_id",
    "gender",
    "class_level",
    "age",
    "attendance_pct",
    "avg_marks",
    "previous_failures",
    "family_income_monthly",
    "distance_to_school_km",
    "guardian_education",
    "single_parent",
    "sibling_dropout",
    "mobile_available",
    "internet_access",
    "scholarship",
    "midday_meal",
    "study_hours_per_day",
    "health_risk",
    "school_engagement_score",
    "teacher_feedback_score",
    "disciplinary_incidents",
]

# Default values for template (example row)
EXAMPLE_ROW = {
    "student_id": 1,
    "gender": "Male",
    "class_level": 9,
    "age": 14,
    "attendance_pct": 85.5,
    "avg_marks": 65.0,
    "previous_failures": 0,
    "family_income_monthly": 12000,
    "distance_to_school_km": 2.5,
    "guardian_education": "Secondary",
    "single_parent": 0,
    "sibling_dropout": 0,
    "mobile_available": 1,
    "internet_access": 1,
    "scholarship": 1,
    "midday_meal": 1,
    "study_hours_per_day": 2.0,
    "health_risk": "Low",
    "school_engagement_score": 0.85,
    "teacher_feedback_score": 0.5,
    "disciplinary_incidents": 0,
}


# ─── Helper Functions ───────────────────────────────────────────

def _generate_template_excel() -> io.BytesIO:
    """Generate template Excel file with headers + 1 example row."""
    output = io.BytesIO()

    # Create DataFrame with headers
    df_template = pd.DataFrame([EXAMPLE_ROW], columns=TEMPLATE_COLUMNS)

    # Write to Excel
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_template.to_excel(writer, sheet_name="Input Data", index=False)

        # Get workbook and format header
        workbook = writer.book
        worksheet = writer.sheets["Input Data"]

        # Bold headers
        from openpyxl.styles import Font, PatternFill, Alignment
        header_fill = PatternFill(start_color="2F6DF6", end_color="2F6DF6", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        example_font = Font(italic=True, color="888888", size=10)

        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        # Format example row (row 2)
        for cell in worksheet[2]:
            cell.font = example_font
            cell.alignment = Alignment(horizontal="center")

        # Auto-adjust column widths
        for col_idx, col_name in enumerate(TEMPLATE_COLUMNS, 1):
            worksheet.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = max(20, len(col_name) + 4)

        # Add instructions sheet
        ws_instructions = workbook.create_sheet("Instructions", 0)
        instructions = [
            ("📋 Dropout Prediction Template Instructions",),
            ("",),
            ("1. Fill the 'Input Data' sheet with student information.",),
            ("2. Each row = one student.",),
            ("3. Column headers must NOT be changed.",),
            ("4. All numeric fields are required.",),
            ("",),
            ("COLUMN DESCRIPTIONS:",),
            ("  student_id           - Unique ID (integer)",),
            ("  gender               - Male / Female",),
            ("  class_level          - 1 to 12",),
            ("  age                  - 6 to 20",),
            ("  attendance_pct       - 0 to 100",),
            ("  avg_marks            - 0 to 100",),
            ("  previous_failures    - Count of previous failures",),
            ("  family_income_monthly - Monthly income in INR",),
            ("  distance_to_school_km - Distance in km",),
            ("  guardian_education   - Primary / Secondary / Graduate / Post Graduate",),
            ("  single_parent        - 0=No, 1=Yes",),
            ("  sibling_dropout      - 0=No, 1=Yes",),
            ("  mobile_available     - 0=No, 1=Yes",),
            ("  internet_access      - 0=No, 1=Yes",),
            ("  scholarship          - 0=No, 1=Yes",),
            ("  midday_meal          - 0=No, 1=Yes",),
            ("  study_hours_per_day  - 0 to 10",),
            ("  health_risk          - Low / Medium / High",),
            ("  school_engagement_score - 0.0 to 1.0",),
            ("  teacher_feedback_score   - 0.0 to 1.0",),
            ("  disciplinary_incidents   - Count",),
            ("",),
            ("OUTPUT:",),
            ("  The output file will contain all input columns + prediction columns:",),
            ("    - dropout_probability (0-100)",),
            ("    - risk_level (Low / Medium / High / Critical)",),
            ("    - recommendation (actionable suggestion)",),
        ]
        for i, (text,) in enumerate(instructions, 1):
            cell = ws_instructions.cell(row=i, column=1, value=text)
            if i == 1:
                cell.font = Font(bold=True, size=14, color="2F6DF6")
            elif text.startswith("COLUMN") or text.startswith("OUTPUT"):
                cell.font = Font(bold=True, size=11, color="333333")
            else:
                cell.font = Font(size=10, color="555555")
        ws_instructions.column_dimensions["A"].width = 80

    output.seek(0)
    return output


def _process_upload_excel(file_bytes: bytes) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """
    Process uploaded Excel file:
      1. Read the 'Input Data' sheet
      2. Validate columns match TEMPLATE_COLUMNS
      3. Run ML predictions
      4. Return enriched DataFrame + row data
    """
    try:
        df = pd.read_excel(io.BytesIO(file_bytes), sheet_name="Input Data")
    except Exception:
        # Try reading first sheet if "Input Data" not found
        try:
            df = pd.read_excel(io.BytesIO(file_bytes))
        except Exception as e:
            raise ValueError(f"Failed to read Excel file: {str(e)}")

    # Validate columns
    missing_cols = [c for c in TEMPLATE_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing columns in uploaded file: {', '.join(missing_cols)}. "
            f"Please download the template and use the correct format."
        )

    # Keep only the columns we need (in correct order)
    df = df[TEMPLATE_COLUMNS]

    # Remove rows where student_id is missing
    df = df.dropna(subset=["student_id"])

    if df.empty:
        raise ValueError("No valid student data found in uploaded file.")

    # Enforce column types
    if "student_id" in df.columns:
        df["student_id"] = df["student_id"].astype(int)

    # Run ML predictions
    predictions_df = predict_batch(df)

    # Combine input + predictions
    result_df = df.copy()
    result_df["dropout_probability"] = predictions_df["dropout_probability"]
    result_df["risk_level"] = predictions_df["risk_level"]
    result_df["recommendation"] = predictions_df["recommendation"]

    # Build row data for JSON response
    rows = result_df.to_dict(orient="records")

    return result_df, rows


# ─── API: GET /template ─────────────────────────────────────────

@router.get(
    "/template",
    summary="Download prediction template Excel",
    description=(
        "Download a template Excel file with all 20 model features as columns. "
        "Fill in student data and upload via POST /dropout/upload-predict."
    ),
    tags=["Dropout Prediction — HM Portal"],
)
async def download_template():
    """Download template Excel for bulk dropout prediction."""
    try:
        excel_buffer = _generate_template_excel()
        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=dropout_prediction_template.xlsx",
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            },
        )
    except Exception as e:
        logger.error("Failed to generate template: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate template: {str(e)}")


# ─── API: POST /upload-predict ──────────────────────────────────

@router.post(
    "/upload-predict",
    summary="Upload Excel and get dropout predictions",
    description=(
        "Upload an Excel file with student features (same format as template). "
        "Returns predicted dropout probabilities, risk levels, and recommendations "
        "as a downloadable Excel file."
    ),
    tags=["Dropout Prediction — HM Portal"],
)
async def upload_and_predict(
    file: UploadFile = File(...),
):
    """
    Upload Excel/CSV file → run ML predictions → return enriched Excel.

    Expected columns (21 total):
        student_id, gender, class_level, age, attendance_pct, avg_marks,
        previous_failures, family_income_monthly, distance_to_school_km,
        guardian_education, single_parent, sibling_dropout, mobile_available,
        internet_access, scholarship, midday_meal, study_hours_per_day,
        health_risk, school_engagement_score, teacher_feedback_score,
        disciplinary_incidents

    Output columns (24 total): all input + dropout_probability, risk_level, recommendation
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Validate file type
    valid_extensions = (".xlsx", ".xls", ".csv")
    if not any(file.filename.lower().endswith(ext) for ext in valid_extensions):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Supported: {', '.join(valid_extensions)}",
        )

    try:
        # Read uploaded file
        contents = await file.read()

        # Process and predict
        result_df, rows = _process_upload_excel(contents)

        # Generate output Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            result_df.to_excel(writer, sheet_name="Predictions", index=False)

            # Format the workbook
            workbook = writer.book
            worksheet = writer.sheets["Predictions"]

            from openpyxl.styles import Font, PatternFill, Alignment

            # Color-code headers
            header_fill = PatternFill(start_color="2F6DF6", end_color="2F6DF6", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF", size=11)

            # Color-code risk levels
            risk_fills = {
                "Critical": PatternFill(start_color="FEF2F2", end_color="FEF2F2", fill_type="solid"),
                "High": PatternFill(start_color="FFF7ED", end_color="FFF7ED", fill_type="solid"),
                "Medium": PatternFill(start_color="FEFCE8", end_color="FEFCE8", fill_type="solid"),
                "Low": PatternFill(start_color="F0FDF4", end_color="F0FDF4", fill_type="solid"),
            }

            risk_col = result_df.columns.get_loc("risk_level") + 1  # 1-based

            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center")

            # Format data rows
            for row_idx in range(2, worksheet.max_row + 1):
                risk_value = worksheet.cell(row=row_idx, column=risk_col).value
                if risk_value and risk_value in risk_fills:
                    for col_idx in range(1, worksheet.max_column + 1):
                        worksheet.cell(row=row_idx, column=col_idx).fill = risk_fills[risk_value]

            # Auto-adjust column widths
            for col_idx, col_name in enumerate(result_df.columns, 1):
                worksheet.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = max(
                    18, len(str(col_name)) + 4
                )

        output.seek(0)

        input_filename = file.filename.rsplit(".", 1)[0]
        output_filename = f"{input_filename}_predictions.xlsx"

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={output_filename}",
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Upload prediction failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


# ─── API: POST /upload-json ────────────────────────────────────
# Upload Excel and return raw data WITHOUT predictions

@router.post(
    "/upload-json",
    summary="Upload Excel and get raw data as JSON (no predictions)",
    description=(
        "Upload an Excel file and return the rows as JSON without running predictions. "
        "Useful for previewing data before predicting. "
        "Call POST /upload-predict-json to also run predictions."
    ),
    tags=["Dropout Prediction — HM Portal"],
)
async def upload_json(
    file: UploadFile = File(...),
):
    """Upload Excel → read rows → return JSON (raw data only, no predictions)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents), sheet_name="Input Data")

        # Validate columns
        missing_cols = [c for c in TEMPLATE_COLUMNS if c not in df.columns]
        if missing_cols:
            raise ValueError(
                f"Missing columns in uploaded file: {', '.join(missing_cols)}. "
                f"Please download the template and use the correct format."
            )

        # Keep only the columns we need (in correct order)
        df = df[TEMPLATE_COLUMNS]
        df = df.dropna(subset=["student_id"])
        df["student_id"] = df["student_id"].astype(int)

        rows = df.to_dict(orient="records")

        return {
            "total": len(rows),
            "students": rows,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Upload JSON failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── API: POST /upload-predict-json ─────────────────────────────
# Upload and get predictions as JSON (for Run button)

@router.post(
    "/upload-predict-json",
    summary="Upload Excel and get predictions as JSON",
    description=(
        "Same as /upload-predict but returns JSON instead of Excel download. "
        "Useful for mobile app integration."
    ),
    tags=["Dropout Prediction — HM Portal"],
)
async def upload_and_predict_json(
    file: UploadFile = File(...),
):
    """Upload Excel → run predictions → return JSON response."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    try:
        contents = await file.read()
        _, rows = _process_upload_excel(contents)

        return {
            "total": len(rows),
            "predictions": rows,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Upload predict JSON failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
