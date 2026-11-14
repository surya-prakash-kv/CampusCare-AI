BEGIN;

ALTER TABLE public.complaints
ADD COLUMN IF NOT EXISTS ai_classification_started_at
TIMESTAMPTZ;

COMMIT;