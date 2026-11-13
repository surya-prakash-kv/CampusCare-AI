
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ComplaintCreateRequest(BaseModel):
    title: str = Field(
        min_length=5,
        max_length=200
    )

    description: str = Field(
        min_length=10,
        max_length=5000
    )

    category: str | None = Field(
        default=None,
        max_length=50
    )

    @field_validator("title", "description")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("This field cannot be empty")

        return value

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None


class ComplaintResponse(BaseModel):
    id: int
    student_id: int
    assigned_admin_id: int | None
    title: str
    description: str
    category: str | None
    priority: Literal["LOW", "MEDIUM", "HIGH", "URGENT"]
    status: Literal["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"]
    created_at: datetime
    updated_at: datetime

class ComplaintStatusUpdateRequest(BaseModel):
    status: Literal[
        "OPEN",
        "IN_PROGRESS",
        "RESOLVED",
        "CLOSED"
    ]

    remarks: str | None = Field(
        default=None,
        max_length=1000
    )

    @field_validator("remarks")
    @classmethod
    def validate_remarks(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None

class ComplaintHistoryResponse(BaseModel):
    id: int
    complaint_id: int
    changed_by: int
    old_status: Literal[
        "OPEN",
        "IN_PROGRESS",
        "RESOLVED",
        "CLOSED"
    ] | None
    new_status: Literal[
        "OPEN",
        "IN_PROGRESS",
        "RESOLVED",
        "CLOSED"
    ]
    remarks: str | None
    created_at: datetime
