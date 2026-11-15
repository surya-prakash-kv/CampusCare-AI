from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from psycopg import OperationalError

from app.main import app
from app.db.connection import get_db


@pytest.fixture
def client():
    app.dependency_overrides.clear()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def setup_login_mocks(monkeypatch, user):
    db = MagicMock()
    cursor = MagicMock()

    db.cursor.return_value.__enter__.return_value = cursor
    cursor.fetchone.return_value = user

    app.dependency_overrides[get_db] = lambda: db

    rate_limit_check = MagicMock(return_value=None)
    record_failure = MagicMock()
    clear_failures = MagicMock()

    monkeypatch.setattr(
        "app.api.auth.create_login_rate_limit_identifiers",
        lambda email, client_ip: ("email-ip-hash", "ip-hash"),
    )
    monkeypatch.setattr(
        "app.api.auth.is_login_rate_limited",
        rate_limit_check,
    )
    monkeypatch.setattr(
        "app.api.auth.record_failed_login",
        record_failure,
    )
    monkeypatch.setattr(
        "app.api.auth.clear_email_ip_failures",
        clear_failures,
    )

    monkeypatch.setattr(
        "app.api.auth.verify_password",
        lambda password, password_hash: True,
    )
    monkeypatch.setattr(
        "app.api.auth.password_needs_rehash",
        lambda password_hash: False,
    )
    monkeypatch.setattr(
        "app.api.auth.hash_password",
        lambda password: "upgraded-argon2-hash",
    )
    monkeypatch.setattr(
        "app.api.auth.create_access_token",
        lambda user_id, role: ("test-access-token", 3600),
    )

    return (
        db,
        cursor,
        rate_limit_check,
        record_failure,
        clear_failures,
    )


def login(client, email="student@example.com"):
    return client.post(
        "/api/auth/login",
        data={
            "username": email,
            "password": "StrongTestPassword123!",
        },
    )


def test_login_with_current_password_hash(client, monkeypatch):
    user = (1, "current-argon2-hash", "STUDENT", True)

    db, cursor, rate_check, record_failure, clear_failures = (
        setup_login_mocks(monkeypatch, user)
    )

    response = login(client)

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "test-access-token",
        "token_type": "bearer",
        "expires_in": 3600,
    }

    rate_check.assert_called_once_with(
        db, "email-ip-hash", "ip-hash"
    )
    clear_failures.assert_called_once_with(db, "email-ip-hash")
    record_failure.assert_not_called()
    assert cursor.execute.call_count == 1


def test_login_rehashes_outdated_password_hash(client, monkeypatch):
    user = (1, "outdated-argon2-hash", "STUDENT", True)

    db, cursor, _, _, _ = setup_login_mocks(monkeypatch, user)

    monkeypatch.setattr(
        "app.api.auth.password_needs_rehash",
        lambda password_hash: True,
    )

    response = login(client)

    assert response.status_code == 200
    assert cursor.execute.call_count == 2

    update_sql = cursor.execute.call_args_list[1].args[0]
    update_params = cursor.execute.call_args_list[1].args[1]

    assert "UPDATE users" in update_sql
    assert "password_hash" in update_sql
    assert "updated_at = CURRENT_TIMESTAMP" in update_sql
    assert update_params == ("upgraded-argon2-hash", 1)


def test_login_with_invalid_password_records_failure(
    client, monkeypatch
):
    user = (1, "current-argon2-hash", "STUDENT", True)

    db, cursor, _, record_failure, clear_failures = (
        setup_login_mocks(monkeypatch, user)
    )

    monkeypatch.setattr(
        "app.api.auth.verify_password",
        lambda password, password_hash: False,
    )

    response = login(client)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

    record_failure.assert_called_once_with(
        db, "email-ip-hash", "ip-hash"
    )
    clear_failures.assert_not_called()
    assert cursor.execute.call_count == 1


def test_inactive_user_cannot_login(client, monkeypatch):
    user = (1, "current-argon2-hash", "STUDENT", False)

    _, cursor, _, record_failure, clear_failures = (
        setup_login_mocks(monkeypatch, user)
    )

    verify_mock = MagicMock(return_value=True)
    monkeypatch.setattr("app.api.auth.verify_password", verify_mock)

    response = login(client)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

    verify_mock.assert_not_called()
    record_failure.assert_called_once()
    clear_failures.assert_not_called()
    assert cursor.execute.call_count == 1


def test_unknown_email_cannot_login(client, monkeypatch):
    _, cursor, _, record_failure, clear_failures = (
        setup_login_mocks(monkeypatch, None)
    )

    response = login(client, "unknown@example.com")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

    record_failure.assert_called_once()
    clear_failures.assert_not_called()
    assert cursor.execute.call_count == 1


def test_rate_limited_login_returns_429_without_password_check(
    client, monkeypatch
):
    user = (1, "current-argon2-hash", "STUDENT", True)

    _, cursor, rate_check, record_failure, clear_failures = (
        setup_login_mocks(monkeypatch, user)
    )

    rate_check.return_value = 437

    verify_mock = MagicMock(return_value=True)
    monkeypatch.setattr("app.api.auth.verify_password", verify_mock)

    response = login(client)

    assert response.status_code == 429
    assert response.json()["detail"] == (
        "Too many failed login attempts. Try again later."
    )
    assert response.headers["Retry-After"] == "437"

    verify_mock.assert_not_called()
    record_failure.assert_not_called()
    clear_failures.assert_not_called()
    cursor.execute.assert_not_called()


def test_rate_limit_database_failure_returns_503(
    client, monkeypatch
):
    _, cursor, rate_check, _, _ = setup_login_mocks(
        monkeypatch, None
    )

    rate_check.side_effect = OperationalError("database unavailable")

    response = login(client)

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Login service temporarily unavailable"
    )
    cursor.execute.assert_not_called()


def test_failed_attempt_storage_error_returns_503(
    client, monkeypatch
):
    user = (1, "current-argon2-hash", "STUDENT", True)

    _, cursor, _, record_failure, _ = setup_login_mocks(
        monkeypatch, user
    )

    monkeypatch.setattr(
        "app.api.auth.verify_password",
        lambda password, password_hash: False,
    )

    record_failure.side_effect = OperationalError(
        "database unavailable"
    )

    response = login(client)

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Login service temporarily unavailable"
    )


def test_successful_login_clearing_failure_error_returns_503(
    client, monkeypatch
):
    user = (1, "current-argon2-hash", "STUDENT", True)

    _, cursor, _, _, clear_failures = setup_login_mocks(
        monkeypatch, user
    )

    clear_failures.side_effect = OperationalError(
        "database unavailable"
    )

    response = login(client)

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Login service temporarily unavailable"
    )
