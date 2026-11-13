import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from psycopg import Connection

from app.db.connection import get_db
from app.services.token import decode_access_token


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Connection = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = decode_access_token(token)

        user_id = int(payload["sub"])

        if user_id <= 0:
            raise ValueError("Invalid user ID")

    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise credentials_exception

    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, full_name, email, role, is_active
            FROM users
            WHERE id = %s;
            """,
            (user_id,)
        )

        user = cursor.fetchone()

    if user is None or not user[4]:
        raise credentials_exception

    return {
        "id": user[0],
        "full_name": user[1],
        "email": user[2],
        "role": user[3]
    }


def require_role(*allowed_roles: str):
    def role_checker(
        current_user: dict = Depends(get_current_user)
    ):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource"
            )

        return current_user

    return role_checker
