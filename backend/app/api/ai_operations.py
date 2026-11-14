
from fastapi import APIRouter, Depends
from psycopg import Connection

from app.core.security import require_role
from app.db.connection import get_db
from app.schemas.ai_metrics import AIOperationsMetricsResponse
from app.services.ai.metrics import get_ai_operations_metrics


router = APIRouter(
    prefix="/api/admin/ai-operations",
    tags=["AI Operations"]
)


@router.get(
    "/metrics",
    response_model=AIOperationsMetricsResponse
)
def read_ai_operations_metrics(
    current_user: dict = Depends(require_role("ADMIN")),
    db: Connection = Depends(get_db),
):
    return get_ai_operations_metrics(db)
