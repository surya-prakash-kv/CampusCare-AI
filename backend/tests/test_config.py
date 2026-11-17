import pytest

from app.core import config


def test_validate_database_config_rejects_missing_settings(monkeypatch):
    monkeypatch.setattr(config, "DB_NAME", None)
    monkeypatch.setattr(config, "DB_USER", None)
    monkeypatch.setattr(config, "DB_PASSWORD", None)

    with pytest.raises(RuntimeError, match="Missing database settings"):
        config.validate_database_config()


def test_validate_database_config_accepts_valid_settings(monkeypatch):
    monkeypatch.setattr(config, "DB_NAME", "campuscare_ai")
    monkeypatch.setattr(config, "DB_USER", "postgres")
    monkeypatch.setattr(config, "DB_PASSWORD", "test-password")

    config.validate_database_config()


def test_validate_jwt_config_accepts_valid_settings(monkeypatch):
    monkeypatch.setattr(config, "JWT_SECRET", "x" * 32)
    monkeypatch.setattr(config, "JWT_ALGORITHM", "HS256")
    monkeypatch.setattr(config, "ACCESS_TOKEN_EXPIRE_MINUTES", 30)

    config.validate_jwt_config()


@pytest.mark.parametrize(
    ("secret", "algorithm", "expiry", "expected_error"),
    [
        (None, "HS256", 30, "JWT_SECRET is not configured"),
        ("short", "HS256", 30, "at least 32 characters"),
        ("x" * 32, "HS512", 30, "Only HS256"),
        ("x" * 32, "HS256", 0, "greater than zero"),
    ],
)
def test_validate_jwt_config_rejects_invalid_settings(
    monkeypatch,
    secret,
    algorithm,
    expiry,
    expected_error,
):
    monkeypatch.setattr(config, "JWT_SECRET", secret)
    monkeypatch.setattr(config, "JWT_ALGORITHM", algorithm)
    monkeypatch.setattr(config, "ACCESS_TOKEN_EXPIRE_MINUTES", expiry)

    with pytest.raises(RuntimeError, match=expected_error):
        config.validate_jwt_config()


@pytest.mark.parametrize(
    "setting",
    [
        "AI_RECOVERY_INTERVAL_SECONDS",
        "AI_RECOVERY_STALE_AFTER_SECONDS",
        "AI_RECOVERY_BATCH_SIZE",
    ],
)
def test_validate_ai_recovery_config_rejects_non_positive_values(
    monkeypatch,
    setting,
):
    monkeypatch.setattr(config, setting, 0)

    with pytest.raises(RuntimeError, match=setting):
        config.validate_ai_recovery_config()


def test_validate_application_config_accepts_valid_settings(monkeypatch):
    monkeypatch.setattr(config, "DB_NAME", "campuscare_ai")
    monkeypatch.setattr(config, "DB_USER", "postgres")
    monkeypatch.setattr(config, "DB_PASSWORD", "test-password")

    monkeypatch.setattr(config, "JWT_SECRET", "x" * 32)
    monkeypatch.setattr(config, "JWT_ALGORITHM", "HS256")
    monkeypatch.setattr(config, "ACCESS_TOKEN_EXPIRE_MINUTES", 30)

    monkeypatch.setattr(config, "AI_RECOVERY_INTERVAL_SECONDS", 30)
    monkeypatch.setattr(config, "AI_RECOVERY_STALE_AFTER_SECONDS", 120)
    monkeypatch.setattr(config, "AI_RECOVERY_BATCH_SIZE", 10)

    config.validate_application_config()


def test_validate_database_config_rejects_non_positive_timeout(
    monkeypatch,
):
    monkeypatch.setattr(config, "DB_NAME", "campuscare_ai")
    monkeypatch.setattr(config, "DB_USER", "postgres")
    monkeypatch.setattr(config, "DB_PASSWORD", "test-password")
    monkeypatch.setattr(config, "DB_CONNECT_TIMEOUT_SECONDS", 0)

    with pytest.raises(
        RuntimeError,
        match="DB_CONNECT_TIMEOUT_SECONDS",
    ):
        config.validate_database_config()

def test_validate_login_rate_limit_config_accepts_valid_settings(monkeypatch):
    monkeypatch.setattr(config, "RATE_LIMIT_HASH_SECRET", "x" * 48)
    monkeypatch.setattr(config, "LOGIN_RATE_LIMIT_EMAIL_IP_MAX_ATTEMPTS", 5)
    monkeypatch.setattr(config, "LOGIN_RATE_LIMIT_IP_MAX_ATTEMPTS", 20)
    monkeypatch.setattr(config, "LOGIN_RATE_LIMIT_WINDOW_SECONDS", 900)
    monkeypatch.setattr(config, "LOGIN_RATE_LIMIT_BLOCK_SECONDS", 900)

    config.validate_login_rate_limit_config()


@pytest.mark.parametrize(
    ("secret", "expected_error"),
    [
        (None, "RATE_LIMIT_HASH_SECRET is not configured"),
        ("short", "at least 32 characters"),
    ],
)
def test_validate_login_rate_limit_config_rejects_invalid_secret(
    monkeypatch,
    secret,
    expected_error,
):
    monkeypatch.setattr(config, "RATE_LIMIT_HASH_SECRET", secret)

    with pytest.raises(RuntimeError, match=expected_error):
        config.validate_login_rate_limit_config()


@pytest.mark.parametrize(
    "setting",
    [
        "LOGIN_RATE_LIMIT_EMAIL_IP_MAX_ATTEMPTS",
        "LOGIN_RATE_LIMIT_IP_MAX_ATTEMPTS",
        "LOGIN_RATE_LIMIT_WINDOW_SECONDS",
        "LOGIN_RATE_LIMIT_BLOCK_SECONDS",
    ],
)
def test_validate_login_rate_limit_config_rejects_non_positive_values(
    monkeypatch,
    setting,
):
    monkeypatch.setattr(config, "RATE_LIMIT_HASH_SECRET", "x" * 48)
    monkeypatch.setattr(config, setting, 0)

    with pytest.raises(RuntimeError, match=setting):
        config.validate_login_rate_limit_config()

def test_validate_environment_config_accepts_development(monkeypatch):
    monkeypatch.setattr(config, "APP_ENV", "development")
    monkeypatch.setattr(config, "CORS_ALLOWED_ORIGINS", ())

    config.validate_environment_config()


def test_validate_environment_config_accepts_production(monkeypatch):
    monkeypatch.setattr(config, "APP_ENV", "production")
    monkeypatch.setattr(
        config,
        "CORS_ALLOWED_ORIGINS",
        ("https://campuscare.example.com",),
    )

    config.validate_environment_config()


@pytest.mark.parametrize(
    "environment",
    ["", "dev", "staging", "invalid"],
)
def test_validate_environment_config_rejects_invalid_environment(
    monkeypatch,
    environment,
):
    monkeypatch.setattr(config, "APP_ENV", environment)

    with pytest.raises(
        RuntimeError,
        match="APP_ENV must be",
    ):
        config.validate_environment_config()


@pytest.mark.parametrize(
    "origin",
    [
        "*",
        "https://*",
        "ftp://campuscare.example.com",
        "https://campuscare.example.com/",
    ],
)
def test_validate_environment_config_rejects_invalid_cors_origins(
    monkeypatch,
    origin,
):
    monkeypatch.setattr(config, "APP_ENV", "production")
    monkeypatch.setattr(
        config,
        "CORS_ALLOWED_ORIGINS",
        (origin,),
    )

    with pytest.raises(
        RuntimeError,
        match="CORS_ALLOWED_ORIGINS",
    ):
        config.validate_environment_config()


@pytest.mark.parametrize(
    "level",
    ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
)
def test_validate_logging_config_accepts_valid_levels(
    monkeypatch,
    level,
):
    monkeypatch.setattr(config, "LOG_LEVEL", level)

    config.validate_logging_config()


@pytest.mark.parametrize(
    "level",
    ["", "INVALID", "TRACE", "123"],
)
def test_validate_logging_config_rejects_invalid_levels(
    monkeypatch,
    level,
):
    monkeypatch.setattr(config, "LOG_LEVEL", level)

    with pytest.raises(
        RuntimeError,
        match="LOG_LEVEL",
    ):
        config.validate_logging_config()

@pytest.mark.parametrize("port", [1, 65535])
def test_validate_database_config_accepts_valid_port_boundaries(
    monkeypatch,
    port,
):
    monkeypatch.setattr(config, "DB_PORT", port)
    monkeypatch.setattr(config, "DB_NAME", "campuscare_ai")
    monkeypatch.setattr(config, "DB_USER", "postgres")
    monkeypatch.setattr(config, "DB_PASSWORD", "test-password")
    monkeypatch.setattr(config, "DB_CONNECT_TIMEOUT_SECONDS", 5)

    config.validate_database_config()


@pytest.mark.parametrize("port", [0, 65536])
def test_validate_database_config_rejects_invalid_port_boundaries(
    monkeypatch,
    port,
):
    monkeypatch.setattr(config, "DB_PORT", port)

    with pytest.raises(
        RuntimeError,
        match="DB_PORT must be between 1 and 65535",
    ):
        config.validate_database_config()


def test_validate_gemini_config_rejects_missing_production_api_key(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", None)

    with pytest.raises(
        RuntimeError,
        match="GEMINI_API_KEY is not configured",
    ):
        config.validate_gemini_config("production")


def test_validate_gemini_config_accepts_valid_production_settings(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "test-gemini-api-key")
    monkeypatch.setattr(config, "GEMINI_MODEL", "gemini-3.5-flash-lite")

    config.validate_gemini_config("production")
