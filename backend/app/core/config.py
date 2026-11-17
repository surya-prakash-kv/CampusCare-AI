
import os

from dotenv import load_dotenv

load_dotenv()


# Application Environment
APP_ENV = os.getenv(
    "APP_ENV",
    "development",
).strip().lower()

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO",
).strip().upper()

CORS_ALLOWED_ORIGINS = tuple(
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "",
    ).split(",")
    if origin.strip()
)

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))

DB_CONNECT_TIMEOUT_SECONDS = int(
    os.getenv("DB_CONNECT_TIMEOUT_SECONDS", "5")
)

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_SSLMODE = os.getenv("DB_SSLMODE", "disable").strip().lower()


# Vercel Cron Configuration
CRON_SECRET = os.getenv("CRON_SECRET")

# AI Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")


# Login Rate Limiting
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


# AI Recovery Configuration
AI_RECOVERY_INTERVAL_SECONDS = int(
    os.getenv("AI_RECOVERY_INTERVAL_SECONDS", "30")
)

AI_RECOVERY_STALE_AFTER_SECONDS = int(
    os.getenv("AI_RECOVERY_STALE_AFTER_SECONDS", "120")
)

AI_RECOVERY_BATCH_SIZE = int(
    os.getenv("AI_RECOVERY_BATCH_SIZE", "10")
)


# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)


def validate_environment_config(environment=None):
    environment = APP_ENV if environment is None else environment
    if environment not in {
        "development",
        "testing",
        "production",
    }:
        raise RuntimeError(
            "APP_ENV must be development, testing, or production"
        )

    for origin in CORS_ALLOWED_ORIGINS:
        if (
            not origin.startswith(("http://", "https://"))
            or "*" in origin
            or origin.endswith("/")
        ):
            raise RuntimeError(
                "CORS_ALLOWED_ORIGINS must contain exact HTTP(S) "
                "origins without wildcards or trailing slashes"
            )


def validate_database_config():
    if not 1 <= DB_PORT <= 65535:
        raise RuntimeError(
            "DB_PORT must be between 1 and 65535"
        )

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

def validate_gemini_config(environment=None):
    environment = APP_ENV if environment is None else environment

    if environment == "production":
        if not GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured"
            )

        if not GEMINI_MODEL.strip():
            raise RuntimeError(
                "GEMINI_MODEL is not configured"
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

def validate_cron_config(environment=None):
    environment = APP_ENV if environment is None else environment

    if environment == "production":
        if not CRON_SECRET:
            raise RuntimeError(
                "CRON_SECRET is not configured"
            )

        if len(CRON_SECRET) < 32:
            raise RuntimeError(
                "CRON_SECRET must contain at least 32 characters"
            )
        
def validate_logging_config():
    import logging

    if not hasattr(logging, LOG_LEVEL):
        raise RuntimeError(
            "LOG_LEVEL must be a valid Python logging level"
        )

    if not isinstance(getattr(logging, LOG_LEVEL), int):
        raise RuntimeError(
            "LOG_LEVEL must be a valid Python logging level"
        )


def validate_application_config(environment=None):
    validate_environment_config(environment)
    validate_database_config()
    validate_jwt_config()
    validate_ai_recovery_config()
    validate_gemini_config(environment)
    validate_login_rate_limit_config()
    validate_cron_config(environment)
    validate_logging_config()
