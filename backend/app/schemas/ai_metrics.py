
from typing import Literal

from pydantic import BaseModel, Field


class AIAttemptDistribution(BaseModel):
    attempt_count: int = Field(ge=0, le=5)
    total: int = Field(ge=0)


class AIOperationsMetricsResponse(BaseModel):
    total_complaints: int = Field(ge=0)

    not_started: int = Field(ge=0)
    pending: int = Field(ge=0)
    completed: int = Field(ge=0)
    failed: int = Field(ge=0)
    skipped: int = Field(ge=0)

    oldest_pending_age_seconds: int = Field(ge=0)

    attempt_distribution: list[AIAttemptDistribution]

    processing_status: Literal[
        "HEALTHY",
        "PROCESSING",
        "IDLE",
        "DEGRADED"
    ]
