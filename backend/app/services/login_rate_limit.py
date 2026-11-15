
import hashlib
import hmac

from psycopg import Connection

from app.core import config


def create_login_rate_limit_identifiers(
    email: str,
    client_ip: str,
) -> tuple[str, str]:
    secret = config.RATE_LIMIT_HASH_SECRET

    if not secret or len(secret) < 32:
        raise RuntimeError("Login rate-limit secret is not configured")

    normalized_email = email.strip().lower()
    normalized_ip = client_ip.strip()

    if not normalized_email or not normalized_ip:
        raise ValueError("Email and client IP are required")

    secret_bytes = secret.encode("utf-8")

    email_ip_hash = hmac.new(
        secret_bytes,
        f"EMAIL_IP:{normalized_email}\0{normalized_ip}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    ip_hash = hmac.new(
        secret_bytes,
        f"IP:{normalized_ip}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return email_ip_hash, ip_hash


def is_login_rate_limited(
    db: Connection,
    email_ip_hash: str,
    ip_hash: str,
) -> int | None:
    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT CEIL(
                EXTRACT(
                    EPOCH FROM (
                        MAX(blocked_until) - CURRENT_TIMESTAMP
                    )
                )
            )::INTEGER
            FROM public.login_rate_limits
            WHERE blocked_until > CURRENT_TIMESTAMP
              AND (
                  (
                      scope = 'EMAIL_IP'
                      AND identifier_hash = %s
                  )
                  OR
                  (
                      scope = 'IP'
                      AND identifier_hash = %s
                  )
              );
            """,
            (email_ip_hash, ip_hash),
        )

        remaining_seconds = cursor.fetchone()[0]

        return remaining_seconds


def _record_failure(
    db: Connection,
    scope: str,
    identifier_hash: str,
    max_attempts: int,
) -> None:
    window_seconds = config.LOGIN_RATE_LIMIT_WINDOW_SECONDS
    block_seconds = config.LOGIN_RATE_LIMIT_BLOCK_SECONDS

    reset_condition = """
        (
            public.login_rate_limits.window_started_at
                <= CURRENT_TIMESTAMP - (%s * INTERVAL '1 second')
            OR (
                public.login_rate_limits.blocked_until IS NOT NULL
                AND public.login_rate_limits.blocked_until <= CURRENT_TIMESTAMP
            )
        )
    """

    next_attempt_count = f"""
        CASE
            WHEN {reset_condition} THEN 1
            ELSE public.login_rate_limits.failed_attempts + 1
        END
    """

    cursor_sql = f"""
        INSERT INTO public.login_rate_limits (
            scope,
            identifier_hash,
            failed_attempts,
            window_started_at,
            blocked_until,
            updated_at
        )
        VALUES (
            %s,
            %s,
            1,
            CURRENT_TIMESTAMP,
            CASE
                WHEN %s <= 1
                THEN CURRENT_TIMESTAMP + (%s * INTERVAL '1 second')
                ELSE NULL
            END,
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (scope, identifier_hash)
        DO UPDATE SET
            failed_attempts = {next_attempt_count},

            window_started_at = CASE
                WHEN {reset_condition}
                THEN CURRENT_TIMESTAMP
                ELSE public.login_rate_limits.window_started_at
            END,

            blocked_until = CASE
                WHEN ({next_attempt_count}) >= %s
                THEN CURRENT_TIMESTAMP + (%s * INTERVAL '1 second')
                ELSE NULL
            END,

            updated_at = CURRENT_TIMESTAMP;
    """

    params = (
        scope,
        identifier_hash,
        max_attempts,
        block_seconds,
        window_seconds,
        window_seconds,
        window_seconds,
        max_attempts,
        block_seconds,
    )

    with db.cursor() as cursor:
        cursor.execute(cursor_sql, params)


def record_failed_login(
    db: Connection,
    email_ip_hash: str,
    ip_hash: str,
) -> None:
    try:
        _record_failure(
            db,
            "EMAIL_IP",
            email_ip_hash,
            config.LOGIN_RATE_LIMIT_EMAIL_IP_MAX_ATTEMPTS,
        )

        _record_failure(
            db,
            "IP",
            ip_hash,
            config.LOGIN_RATE_LIMIT_IP_MAX_ATTEMPTS,
        )

        # Persist failed attempts before the API returns HTTP 401.
        db.commit()

    except Exception:
        db.rollback()
        raise


def clear_email_ip_failures(
    db: Connection,
    email_ip_hash: str,
) -> None:
    with db.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM public.login_rate_limits
            WHERE scope = 'EMAIL_IP'
              AND identifier_hash = %s;
            """,
            (email_ip_hash,),
        )


def cleanup_expired_login_rate_limits(db: Connection) -> int:
    """
    Delete login rate-limit records that can no longer affect login attempts.

    Active blocks and unexpired failure windows are preserved.
    The caller is responsible for committing or rolling back.
    """
    window_seconds = config.LOGIN_RATE_LIMIT_WINDOW_SECONDS

    with db.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM public.login_rate_limits
            WHERE (
                blocked_until IS NULL
                AND window_started_at
                    <= CURRENT_TIMESTAMP - (%s * INTERVAL '1 second')
            )
            OR (
                blocked_until IS NOT NULL
                AND blocked_until <= CURRENT_TIMESTAMP
            );
            """,
            (window_seconds,),
        )

        return cursor.rowcount
