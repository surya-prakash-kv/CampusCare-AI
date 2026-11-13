
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from datetime import datetime


ComplaintCategory = Literal[
    "ACADEMIC",
    "EXAMINATION",
    "FEES_FINANCE",
    "SCHOLARSHIP",
    "HOSTEL",
    "FOOD_CANTEEN",
    "TRANSPORT",
    "LIBRARY",
    "LABORATORY",
    "IT_SUPPORT",
    "FACILITIES_MAINTENANCE",
    "ADMINISTRATION",
    "HEALTH_AND_SAFETY",
    "STUDENT_WELFARE",
    "OTHER",
]

ComplaintPriority = Literal[
    "LOW",
    "MEDIUM",
    "HIGH",
    "URGENT",
]

ReviewDecision = Literal[
    "ACCEPTED",
    "REJECTED",
    "MODIFIED",
]


class AIReviewRequest(BaseModel):
    decision: ReviewDecision

    final_category: ComplaintCategory | None = None

    final_priority: ComplaintPriority | None = None

    remarks: str | None = Field(
        default=None,
        max_length=1000,
    )

    @model_validator(mode="after")
    def validate_review_decision(self):
        if self.decision == "MODIFIED":
            if self.final_category is None:
                raise ValueError(
                    "Final category is required for MODIFIED decisions"
                )

            if self.final_priority is None:
                raise ValueError(
                    "Final priority is required for MODIFIED decisions"
                )

        elif (
            self.final_category is not None
            or self.final_priority is not None
        ):
            raise ValueError(
                "Final category and priority are only allowed "
                "for MODIFIED decisions"
            )

        if self.remarks is not None:
            self.remarks = self.remarks.strip() or None

        return self


class AIReviewResponse(BaseModel):
    id: int
    complaint_id: int
    reviewed_by: int
    decision: ReviewDecision

    ai_suggested_category: ComplaintCategory
    ai_suggested_priority: ComplaintPriority
    ai_confidence: float = Field(ge=0.0, le=1.0)
    ai_model: str

    original_category: ComplaintCategory | None
    original_priority: ComplaintPriority

    final_category: ComplaintCategory | None
    final_priority: ComplaintPriority

    remarks: str | None
    reviewed_at: datetime


class PendingAIReviewResponse(BaseModel):
    id: int
    student_id: int
    title: str
    description: str
    category: ComplaintCategory | None
    priority: ComplaintPriority

    ai_suggested_category: ComplaintCategory
    ai_suggested_priority: ComplaintPriority
    ai_confidence: float = Field(ge=0.0, le=1.0)
    ai_reason: str | None
    ai_model: str
    ai_classification_status: Literal["COMPLETED"]
    created_at: datetime
