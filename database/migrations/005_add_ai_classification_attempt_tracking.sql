
BEGIN;

ALTER TABLE public.complaints
ADD COLUMN IF NOT EXISTS ai_classification_attempt_id UUID;

ALTER TABLE public.complaints
ADD COLUMN IF NOT EXISTS ai_classification_attempt_count INTEGER
NOT NULL DEFAULT 0;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'complaints_ai_classification_attempt_count_check'
          AND conrelid = 'public.complaints'::regclass
    ) THEN
        ALTER TABLE public.complaints
        ADD CONSTRAINT complaints_ai_classification_attempt_count_check
        CHECK (
            ai_classification_attempt_count BETWEEN 0 AND 5
        );
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS
    idx_complaints_ai_pending_started_at
ON public.complaints (ai_classification_started_at)
WHERE ai_classification_status = 'PENDING';

COMMIT;
