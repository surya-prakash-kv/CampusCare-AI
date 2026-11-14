
from psycopg import Connection

from app.repositories.ai_metrics import (
    get_ai_classification_metrics,
)


def get_ai_operations_metrics(db: Connection) -> dict:
    metrics = get_ai_classification_metrics(db)

    pending = metrics["pending"]
    failed = metrics["failed"]
    not_started = metrics["not_started"]
    total = metrics["total_complaints"]

    if failed > 0:
        processing_status = "DEGRADED"
    elif pending > 0:
        processing_status = "PROCESSING"
    elif total == 0 or not_started > 0:
        processing_status = "IDLE"
    else:
        processing_status = "HEALTHY"

    metrics["processing_status"] = processing_status

    return metrics
