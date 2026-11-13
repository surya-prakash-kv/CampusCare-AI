from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import Connection
from psycopg.errors import UniqueViolation

from app.db.connection import get_db
from app.schemas.auth import (
    StudentRegisterRequest,
    StudentRegisterResponse
)
from app.services.password import hash_password


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=StudentRegisterResponse
)
def register_student(
    student: StudentRegisterRequest,
    db: Connection = Depends(get_db)
):
    password_hash = hash_password(student.password)

    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (
                    full_name,
                    email,
                    password_hash,
                    role
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id, full_name, email, role;
                """,
                (
                    student.full_name,
                    student.email,
                    password_hash,
                    "STUDENT"
                )
            )

            new_student = cursor.fetchone()

        return {
            "message": "Student registered successfully",
            "student": {
                "id": new_student[0],
                "full_name": new_student[1],
                "email": new_student[2],
                "role": new_student[3]
            }
        }

    except UniqueViolation:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address is already registered"
        )
