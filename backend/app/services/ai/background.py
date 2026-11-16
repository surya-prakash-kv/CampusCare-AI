
import logging
from uuid import UUID

from app.core.config import GEMINI_MODEL
from app.db.connection import get_db_connection
from app.repositories.complaint import (
    update_ai_classification,
)
from app.services.ai.classifier import classify_complaint


logger = logging.getLogger(__name__)


def process_complaint_classification(
    complaint_id: int,
    title: str,
    description: str,
    attempt_id: UUID,
):
    try:
        classification = classify_complaint(
            title=title,
            description=description,
        )

        with get_db_connection() as db:
            if classification is None:
                with db.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE complaints
                        SET ai_classification_status = 'SKIPPED'
                        WHERE id = %s
                          AND ai_classification_status = 'PENDING'
                          AND ai_classification_attempt_id = %s;
                        """,
                        (complaint_id, attempt_id),
                    )

                    updated = cursor.rowcount == 1

                if updated:
                    logger.info(
                        "AI classification skipped for complaint %s.",
                        complaint_id,
                    )
                else:
                    logger.warning(
                        "Skip status was not persisted because "
                        "attempt %s no longer owns complaint %s.",
                        attempt_id,
                        complaint_id,
                    )

                return

            updated = update_ai_classification(
                db=db,
                complaint_id=complaint_id,
                attempt_id=attempt_id,
                suggested_category=classification.suggested_category,
                suggested_priority=classification.suggested_priority,
                confidence=classification.confidence,
                reason=classification.reason,
                model=GEMINI_MODEL,
            )

            if updated:
                logger.info(
                    "AI classification completed successfully "
                    "for complaint %s using model %s.",
                    complaint_id,
                    GEMINI_MODEL,
                )
            else:
                logger.warning(
                    "AI classification result was not persisted "
                    "because attempt %s no longer owns complaint %s.",
                    attempt_id,
                    complaint_id,
                )

    except Exception:
        logger.exception(
            "Background AI classification failed for complaint %s.",
            complaint_id,
        )

        try:
            with get_db_connection() as db:
                with db.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE complaints
                        SET
                            ai_classification_status = 'FAILED',
                            ai_classification_started_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                          AND ai_classification_status = 'PENDING'
                          AND ai_classification_attempt_id = %s;
                        """,
                        (complaint_id, attempt_id),
                    )

                    if cursor.rowcount != 1:
                        logger.warning(
                            "Failure status was not persisted because "
                            "attempt %s no longer owns complaint %s.",
                            attempt_id,
                            complaint_id,
                        )

        except Exception:
            logger.exception(
                "Could not update AI failure status for complaint %s.",
                complaint_id,
            )
