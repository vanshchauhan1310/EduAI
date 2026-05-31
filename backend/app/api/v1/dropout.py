from fastapi import APIRouter
from app.ai.dropout.train import train

router = APIRouter()

@router.post("/run-training")
def run_training():

    train()

    return {
        "message": "Training Complete"
    }