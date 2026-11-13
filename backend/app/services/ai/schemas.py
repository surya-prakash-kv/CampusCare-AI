from typing import Literal

from pydantic import BaseModel, Field


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


class ComplaintClassification(BaseModel):
    suggested_category: ComplaintCategory
    suggested_priority: ComplaintPriority
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1, max_length=500)
