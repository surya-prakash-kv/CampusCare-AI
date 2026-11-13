BEGIN;

CREATE TABLE IF NOT EXISTS public.complaint_ai_reviews (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    complaint_id BIGINT NOT NULL
        REFERENCES public.complaints(id),

    reviewed_by BIGINT NOT NULL
        REFERENCES public.users(id),

    decision VARCHAR(20) NOT NULL
        CHECK (
            decision IN (
                'ACCEPTED',
                'REJECTED',
                'MODIFIED'
            )
        ),

    ai_suggested_category VARCHAR(50) NOT NULL,

    ai_suggested_priority VARCHAR(20) NOT NULL
        CHECK (
            ai_suggested_priority IN (
                'LOW',
                'MEDIUM',
                'HIGH',
                'URGENT'
            )
        ),

    ai_confidence NUMERIC(5,4) NOT NULL
        CHECK (
            ai_confidence >= 0
            AND ai_confidence <= 1
        ),

    ai_model VARCHAR(100) NOT NULL,

    original_category VARCHAR(50),

    original_priority VARCHAR(20) NOT NULL
        CHECK (
            original_priority IN (
                'LOW',
                'MEDIUM',
                'HIGH',
                'URGENT'
            )
        ),

    final_category VARCHAR(50),

    final_priority VARCHAR(20) NOT NULL
        CHECK (
            final_priority IN (
                'LOW',
                'MEDIUM',
                'HIGH',
                'URGENT'
            )
        ),

    remarks TEXT,

    reviewed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS
    idx_complaint_ai_reviews_complaint_id
ON public.complaint_ai_reviews(complaint_id);

CREATE INDEX IF NOT EXISTS
    idx_complaint_ai_reviews_reviewed_by
ON public.complaint_ai_reviews(reviewed_by);

COMMIT;
