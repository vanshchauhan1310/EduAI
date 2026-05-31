from fastapi import APIRouter, UploadFile, File
from app.services.dropout_batch_service import process_excel

router = APIRouter()

@router.post("/predict-excel")
async def predict_excel(
    file: UploadFile = File(...)
):
    return await process_excel(file)