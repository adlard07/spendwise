from fastapi import APIRouter, Depends

from src.extras.repository import ExtrasRepository
from src.models.metrics import RequestMetrics

router = APIRouter(prefix="/extras", tags=["extras", "dashboard"])


@router.post("/")
def get_metrics(
    payload: RequestMetrics,
):
    required_fields = payload.required_fields
    user_id = payload.user_id
    extras = ExtrasRepository()
    metrics = extras.get_metrics(required=required_fields, user_id=user_id)

    return {
        "metrics": metrics,
    }
