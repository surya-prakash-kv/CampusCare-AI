import os

from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_CONNECT_TIMEOUT_SECONDS = int(
    os.getenv("DB_CONNECT_TIMEOUT_SECONDS", "5")
)
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

RATE_LIMIT_HASH_SECRET = os.getenv("RATE_LIMIT_HASH_SECRET")

LOGIN_RATE_LIMIT_EMAIL_IP_MAX_ATTEMPTS = int(
    os.getenv("LOGIN_RATE_LIMIT_EMAIL_IP_MAX_ATTEMPTS", "5")
)

LOGIN_RATE_LIMIT_IP_MAX_ATTEMPTS = int(
    os.getenv("LOGIN_RATE_LIMIT_IP_MAX_ATTEMPTS", "20")
)

LOGIN_RATE_LIMIT_WINDOW_SECONDS = int(
    os.getenv("LOGIN_RATE_LIMIT_WINDOW_SECONDS", "900")
)

LOGIN_RATE_LIMIT_BLOCK_SECONDS = int(
    os.getenv("LOGIN_RATE_LIMIT_BLOCK_SECONDS", "900")
)

AI_RECOVERY_INTERVAL_SECONDS = int(
    os.getenv("AI_RECOVERY_INTERVAL_SECONDS", "30")
)

AI_RECOVERY_STALE_AFTER_SECONDS = int(
    os.getenv("AI_RECOVERY_STALE_AFTER_SECONDS", "120")
)

AI_RECOVERY_BATCH_SIZE = int(
    os.getenv("AI_RECOVERY_BATCH_SIZE", "10")
)


def validate_database_config():
    required_settings = {
        "DB_NAME": DB_NAME,
        "DB_USER": DB_USER,
        "DB_PASSWORD": DB_PASSWORD,
    }

    missing_settings = [
        name
        for name, value in required_settings.items()
        if not value
    ]

    if missing_settings:
        raise RuntimeError(
            "Missing database settings: "
            + ", ".join(missing_settings)
        )

    if DB_CONNECT_TIMEOUT_SECONDS <= 0:
        raise RuntimeError(
            "DB_CONNECT_TIMEOUT_SECONDS must be greater than zero"
        )


JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)


def validate_jwt_config():
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET is not configured")

    if len(JWT_SECRET) < 32:
        raise RuntimeError(
            "JWT_SECRET must contain at least 32 characters"
        )

    if JWT_ALGORITHM != "HS256":
        raise RuntimeError(
            "Only HS256 JWT algorithm is supported"
        )

    if ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
        raise RuntimeError(
            "Token expiration must be greater than zero"
        )


def validate_ai_recovery_config():
    settings = {
        "AI_RECOVERY_INTERVAL_SECONDS": AI_RECOVERY_INTERVAL_SECONDS,
        "AI_RECOVERY_STALE_AFTER_SECONDS": AI_RECOVERY_STALE_AFTER_SECONDS,
        "AI_RECOVERY_BATCH_SIZE": AI_RECOVERY_BATCH_SIZE,
    }

    invalid_settings = [
        name
        for name, value in settings.items()
        if value <= 0
    ]

    if invalid_settings:
        raise RuntimeError(
            "AI recovery settings must be positive: "
            + ", ".join(invalid_settings)
        )

def validate_login_rate_limit_config():
    if not RATE_LIMIT_HASH_SECRET:
        raise RuntimeError(
            "RATE_LIMIT_HASH_SECRET is not configured"
        )

    if len(RATE_LIMIT_HASH_SECRET) < 32:
        raise RuntimeError(
            "RATE_LIMIT_HASH_SECRET must contain at least 32 characters"
        )

    settings = {
        "LOGIN_RATE_LIMIT_EMAIL_IP_MAX_ATTEMPTS": (
            LOGIN_RATE_LIMIT_EMAIL_IP_MAX_ATTEMPTS
        ),
        "LOGIN_RATE_LIMIT_IP_MAX_ATTEMPTS": (
            LOGIN_RATE_LIMIT_IP_MAX_ATTEMPTS
        ),
        "LOGIN_RATE_LIMIT_WINDOW_SECONDS": (
            LOGIN_RATE_LIMIT_WINDOW_SECONDS
        ),
        "LOGIN_RATE_LIMIT_BLOCK_SECONDS": (
            LOGIN_RATE_LIMIT_BLOCK_SECONDS
        ),
    }

    invalid_settings = [
        name
        for name, value in settings.items()
        if value <= 0
    ]

    if invalid_settings:
        raise RuntimeError(
            "Login rate-limit settings must be positive: "
            + ", ".join(invalid_settings)
        )


def validate_application_config():
    validate_database_config()
    validate_jwt_config()
    validate_ai_recovery_config()
    validate_login_rate_limit_config()
