import hashlib
import hmac
from unittest.mock import MagicMock

import pytest

from app.core import config
from app.services.login_rate_limit import (
    create_login_rate_limit_identifiers,
    is_login_rate_limited,
    record_failed_login,
    clear_email_ip_failures,
    cleanup_expired_login_rate_limits,
)


@pytest.fixture
def db():
    connection = MagicMock()
    cursor = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    return connection, cursor


def test_identifiers_are_stable_and_normalized(monkeypatch):
    monkeypatch.setattr(config, "RATE_LIMIT_HASH_SECRET", "a" * 40)

    first = create_login_rate_limit_identifiers(
        " Student@Example.com ",
        "127.0.0.1",
    )
    second = create_login_rate_limit_identifiers(
        "student@example.com",
        "127.0.0.1",
    )

    assert first == second
    assert len(first[0]) == 64
    assert len(first[1]) == 64


def test_identifiers_change_for_different_ip(monkeypatch):
    monkeypatch.setattr(config, "RATE_LIMIT_HASH_SECRET", "a" * 40)

    first = create_login_rate_limit_identifiers(
        "student@example.com", "127.0.0.1"
    )
    second = create_login_rate_limit_identifiers(
        "student@example.com", "127.0.0.2"
    )

    assert first[0] != second[0]
    assert first[1] != second[1]


def test_identifiers_reject_missing_secret(monkeypatch):
    monkeypatch.setattr(config, "RATE_LIMIT_HASH_SECRET", None)

    with pytest.raises(RuntimeError):
        create_login_rate_limit_identifiers(
            "student@example.com", "127.0.0.1"
        )


def test_identifiers_reject_empty_email_or_ip(monkeypatch):
    monkeypatch.setattr(config, "RATE_LIMIT_HASH_SECRET", "a" * 40)

    with pytest.raises(ValueError):
        create_login_rate_limit_identifiers("", "127.0.0.1")

    with pytest.raises(ValueError):
        create_login_rate_limit_identifiers(
            "student@example.com", " "
        )


def test_identifiers_use_hmac_sha256(monkeypatch):
    secret = "a" * 40
    monkeypatch.setattr(config, "RATE_LIMIT_HASH_SECRET", secret)

    email_hash, ip_hash = create_login_rate_limit_identifiers(
        "student@example.com", "127.0.0.1"
    )

    expected_email_hash = hmac.new(
        secret.encode(),
        b"EMAIL_IP:student@example.com\0" + b"127.0.0.1",
        hashlib.sha256,
    ).hexdigest()

    expected_ip_hash = hmac.new(
        secret.encode(),
        b"IP:127.0.0.1",
        hashlib.sha256,
    ).hexdigest()

    assert email_hash == expected_email_hash
    assert ip_hash == expected_ip_hash


def test_is_login_rate_limited_returns_none_when_not_blocked(db):
    connection, cursor = db
    cursor.fetchone.return_value = (None,)

    result = is_login_rate_limited(
        connection, "email-ip-hash", "ip-hash"
    )

    assert result is None
    cursor.execute.assert_called_once()


def test_is_login_rate_limited_returns_remaining_seconds(db):
    connection, cursor = db
    cursor.fetchone.return_value = (420,)

    result = is_login_rate_limited(
        connection, "email-ip-hash", "ip-hash"
    )

    assert result == 420


def test_is_login_rate_limited_supports_ip_wide_block(db):
    connection, cursor = db
    cursor.fetchone.return_value = (720,)

    result = is_login_rate_limited(
        connection, "email-ip-hash", "ip-hash"
    )

    assert result == 720


def test_is_login_rate_limited_returns_longest_remaining_duration(db):
    connection, cursor = db
    cursor.fetchone.return_value = (850,)

    result = is_login_rate_limited(
        connection, "email-ip-hash", "ip-hash"
    )

    assert result == 850

    sql = cursor.execute.call_args.args[0]
    assert "MAX(blocked_until)" in sql
    assert "CEIL(" in sql


def test_cleanup_expired_login_rate_limits_deletes_eligible_rows(db, monkeypatch):
    connection, cursor = db
    cursor.rowcount = 3
    monkeypatch.setattr(config, "LOGIN_RATE_LIMIT_WINDOW_SECONDS", 900)

    deleted_count = cleanup_expired_login_rate_limits(connection)

    assert deleted_count == 3
    cursor.execute.assert_called_once()

    sql = cursor.execute.call_args.args[0]
    params = cursor.execute.call_args.args[1]

    assert "blocked_until IS NULL" in sql
    assert "window_started_at" in sql
    assert "blocked_until <= CURRENT_TIMESTAMP" in sql
    assert params == (900,)


def test_cleanup_expired_login_rate_limits_returns_zero_when_nothing_deleted(db):
    connection, cursor = db
    cursor.rowcount = 0

    deleted_count = cleanup_expired_login_rate_limits(connection)

    assert deleted_count == 0
    connection.commit.assert_not_called()
