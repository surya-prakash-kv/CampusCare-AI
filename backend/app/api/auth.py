import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from psycopg import Connection, Error as PsycopgError
from psycopg.errors import UniqueViolation

from app.core import config
from app.core.security import require_role
from app.db.connection import get_db
from app.schemas.auth import (
    StudentRegisterRequest,
    StudentRegisterResponse,
    TokenResponse,
)
from app.services.password import (
    hash_password,
    verify_password,
    password_needs_rehash,
)
from app.services.token import create_access_token
from app.services.login_rate_limit import (
    create_login_rate_limit_identifiers,
    is_login_rate_limited,
    record_failed_login,
    clear_email_ip_failures,
)

logger = logging.getLogger(__name__)


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
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Connection = Depends(get_db),
):
    normalized_email = form_data.username.strip().lower()

    client_ip = (
        request.client.host
        if request.client is not None
        else None
    )

    if not client_ip:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Login service temporarily unavailable",
        )

    try:
        email_ip_hash, ip_hash = create_login_rate_limit_identifiers(
            normalized_email,
            client_ip,
        )

        retry_after = is_login_rate_limited(
            db,
            email_ip_hash,
            ip_hash,
        )

        if retry_after is not None:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Try again later.",
                headers={
                    "Retry-After": str(retry_after)
                },
            )

    except HTTPException:
        raise

    except (PsycopgError, RuntimeError, ValueError):
        logger.exception("Login rate-limit verification failed")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Login service temporarily unavailable",
        )

    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, password_hash, role, is_active
            FROM users
            WHERE email = %s;
            """,
            (normalized_email,),
        )

        user = cursor.fetchone()

    password_valid = (
        user is not None
        and user[3]
        and verify_password(form_data.password, user[1])
    )

    if not password_valid:
        try:
            record_failed_login(
                db,
                email_ip_hash,
                ip_hash,
            )

        except PsycopgError:
            logger.exception("Failed to persist login failure")

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Login service temporarily unavailable",
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        clear_email_ip_failures(db, email_ip_hash)

    except PsycopgError:
        logger.exception("Failed to clear successful login failures")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Login service temporarily unavailable",
        )

    if password_needs_rehash(user[1]):
        upgraded_password_hash = hash_password(form_data.password)

        with db.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET password_hash = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s;
                """,
                (upgraded_password_hash, user[0]),
            )

    access_token, expires_in = create_access_token(
        user_id=user[0],
        role=user[2],
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in,
    }

@router.get("/me")
def read_current_user(
    current_user: dict = Depends(require_role("STUDENT"))
):
    return current_user
