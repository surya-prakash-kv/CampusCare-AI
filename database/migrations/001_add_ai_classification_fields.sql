
BEGIN;

ALTER TABLE public.complaints
ADD COLUMN IF NOT EXISTS ai_suggested_priority VARCHAR(20);

ALTER TABLE public.complaints
ADD COLUMN IF NOT EXISTS ai_reason VARCHAR(500);

ALTER TABLE public.complaints
ADD COLUMN IF NOT EXISTS ai_classification_status VARCHAR(20)
NOT NULL DEFAULT 'NOT_STARTED';

ALTER TABLE public.complaints
ADD COLUMN IF NOT EXISTS ai_model VARCHAR(100);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'complaints_ai_suggested_priority_check'
          AND conrelid = 'public.complaints'::regclass
    ) THEN
        ALTER TABLE public.complaints
        ADD CONSTRAINT complaints_ai_suggested_priority_check
        CHECK (
            ai_suggested_priority IS NULL
            OR ai_suggested_priority IN (
                'LOW', 'MEDIUM', 'HIGH', 'URGENT'
            )
        );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'complaints_ai_classification_status_check'
          AND conrelid = 'public.complaints'::regclass
    ) THEN
        ALTER TABLE public.complaints
        ADD CONSTRAINT complaints_ai_classification_status_check
        CHECK (
            ai_classification_status IN (
                'NOT_STARTED',
                'PENDING',
                'COMPLETED',
                'FAILED',
                'SKIPPED'
            )
        );
    END IF;
END $$;

COMMIT;
