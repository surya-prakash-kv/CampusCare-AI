from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


class StudentRegisterRequest(BaseModel):
    full_name: str = Field(
        min_length=2,
        max_length=100
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128
    )

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 2:
            raise ValueError("Full name must contain at least 2 characters")

        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class RegisteredStudent(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: Literal["STUDENT"]


class StudentRegisterResponse(BaseModel):
    message: str
    student: RegisteredStudent
