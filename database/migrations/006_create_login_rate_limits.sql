BEGIN;

CREATE TABLE IF NOT EXISTS public.login_rate_limits (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    scope VARCHAR(16) NOT NULL
        CHECK (scope IN ('EMAIL_IP', 'IP')),

    identifier_hash CHAR(64) NOT NULL,

    failed_attempts INTEGER NOT NULL DEFAULT 0
        CHECK (failed_attempts >= 0),

    window_started_at TIMESTAMPTZ NOT NULL,

    blocked_until TIMESTAMPTZ,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT login_rate_limits_scope_identifier_unique
        UNIQUE (scope, identifier_hash),

    CONSTRAINT login_rate_limits_blocked_until_check
        CHECK (
            blocked_until IS NULL
            OR blocked_until >= window_started_at
        )
);

CREATE INDEX IF NOT EXISTS
    idx_login_rate_limits_updated_at
ON public.login_rate_limits (updated_at);

CREATE INDEX IF NOT EXISTS
    idx_login_rate_limits_blocked_until
ON public.login_rate_limits (blocked_until)
WHERE blocked_until IS NOT NULL;


INSERT INTO public.schema_migrations (
    version,
    description
)
VALUES (
    '006',
    'Create login rate limits table'
)
ON CONFLICT (version) DO NOTHING;

COMMIT;
