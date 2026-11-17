import hmac

from fastapi import APIRouter, Header, HTTPException, status

from app.core.config import CRON_SECRET
from app.services.ai.recovery import recover_stale_classifications


router = APIRouter(
    prefix="/api/internal",
    tags=["Internal Operations"],
)


@router.api_route(
    "/ai-recovery",
    methods=["GET", "POST"],
)
def trigger_ai_recovery(
    authorization: str | None = Header(default=None),
):
    if not CRON_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cron authentication is not configured",
        )

    expected_authorization = f"Bearer {CRON_SECRET}"

    if not authorization or not hmac.compare_digest(
        authorization,
        expected_authorization,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid cron authorization",
        )

    recover_stale_classifications()

    return {
        "status": "completed",
        "operation": "ai-classification-recovery",
    }