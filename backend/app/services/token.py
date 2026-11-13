from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import (
    JWT_SECRET,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    validate_jwt_config
)


def create_access_token(
    user_id: int,
    role: str
) -> tuple[str, int]:
    validate_jwt_config()

    expires_in = ACCESS_TOKEN_EXPIRE_MINUTES * 60

    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(seconds=expires_in)

    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": issued_at,
        "exp": expires_at
    }

    access_token = jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )

    return access_token, expires_in


def decode_access_token(token: str) -> dict:
    validate_jwt_config()

    return jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM]
    )