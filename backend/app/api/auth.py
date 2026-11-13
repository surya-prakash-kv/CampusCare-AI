from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from psycopg import Connection
from psycopg.errors import UniqueViolation

from app.db.connection import get_db
from app.schemas.auth import (
    StudentRegisterRequest,
    StudentRegisterResponse,
    TokenResponse
)
from app.services.password import hash_password, verify_password
from app.services.token import create_access_token
from app.core.security import get_current_user


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

@router.post(
    "/login",
    response_model=TokenResponse
)
def login_student(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Connection = Depends(get_db)
):
    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, password_hash, role, is_active
            FROM users
            WHERE email = %s;
            """,
            (form_data.username.lower(),)
        )

        user = cursor.fetchone()

    if (
        user is None
        or not user[3]
        or not verify_password(form_data.password, user[1])
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token, expires_in = create_access_token(
        user_id=user[0],
        role=user[2]
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in
    }

@router.get("/me")
def read_current_user(
    current_user: dict = Depends(get_current_user)
):
    return current_user