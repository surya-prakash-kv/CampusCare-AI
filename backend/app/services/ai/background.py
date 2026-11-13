import logging

from app.core.config import OPENAI_MODEL
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
                          AND ai_classification_status = 'PENDING';
                        """,
                        (complaint_id,)
                    )

                logger.info(
                    "AI classification skipped for complaint %s.",
                    complaint_id,
                )
                return

            updated = update_ai_classification(
                db=db,
                complaint_id=complaint_id,
                suggested_category=classification.suggested_category,
                suggested_priority=classification.suggested_priority,
                confidence=classification.confidence,
                reason=classification.reason,
                model=OPENAI_MODEL,
            )

            if not updated:
                logger.warning(
                    "AI classification result was not persisted "
                    "for complaint %s.",
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
                        SET ai_classification_status = 'FAILED'
                        WHERE id = %s
                          AND ai_classification_status = 'PENDING';
                        """,
                        (complaint_id,)
                    )
        except Exception:
            logger.exception(
                "Could not update AI failure status for complaint %s.",
                complaint_id,
            )
