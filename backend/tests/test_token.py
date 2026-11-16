import time

import jwt
import pytest

from app.services import token


@pytest.fixture
def jwt_config(monkeypatch):
    monkeypatch.setattr(token, "JWT_SECRET", "t" * 64)
    monkeypatch.setattr(token, "JWT_ALGORITHM", "HS256")
    monkeypatch.setattr(token, "ACCESS_TOKEN_EXPIRE_MINUTES", 30)
    monkeypatch.setattr(token, "validate_jwt_config", lambda: None)


def test_create_access_token_contains_expected_claims(
    jwt_config,
):
    access_token, expires_in = token.create_access_token(
        user_id=123,
        role="STUDENT",
    )

    payload = token.decode_access_token(access_token)

    assert payload["sub"] == "123"
    assert payload["role"] == "STUDENT"
    assert "iat" in payload
    assert "exp" in payload
    assert expires_in == 1800
    assert payload["exp"] > payload["iat"]


def test_create_access_token_uses_configured_expiration(
    jwt_config,
):
    _, expires_in = token.create_access_token(
        user_id=123,
        role="ADMIN",
    )

    assert expires_in == 30 * 60


def test_decode_access_token_rejects_expired_token(
    jwt_config,
):
    expired_token = jwt.encode(
        {
            "sub": "123",
            "role": "STUDENT",
            "iat": int(time.time()) - 120,
            "exp": int(time.time()) - 60,
        },
        token.JWT_SECRET,
        algorithm=token.JWT_ALGORITHM,
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        token.decode_access_token(expired_token)


def test_decode_access_token_rejects_invalid_signature(
    jwt_config,
):
    invalid_token = jwt.encode(
        {
            "sub": "123",
            "role": "STUDENT",
            "exp": int(time.time()) + 300,
        },
        "different-secret" * 3,
        algorithm="HS256",
    )

    with pytest.raises(jwt.InvalidSignatureError):
        token.decode_access_token(invalid_token)


def test_decode_access_token_rejects_malformed_token(
    jwt_config,
):
    with pytest.raises(jwt.DecodeError):
        token.decode_access_token("not-a-valid-jwt")


def test_decode_access_token_rejects_unsupported_algorithm(
    jwt_config,
):
    unsupported_token = jwt.encode(
        {
            "sub": "123",
            "role": "STUDENT",
            "exp": int(time.time()) + 300,
        },
        token.JWT_SECRET,
        algorithm="HS512",
    )

    with pytest.raises(jwt.InvalidAlgorithmError):
        token.decode_access_token(unsupported_token)
