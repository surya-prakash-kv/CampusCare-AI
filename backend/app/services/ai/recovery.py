
import logging
from concurrent.futures import ThreadPoolExecutor

from app.core.config import (
    AI_RECOVERY_BATCH_SIZE,
    AI_RECOVERY_STALE_AFTER_SECONDS,
)
from app.db.connection import get_db_connection
from app.repositories.complaint import (
    recover_stale_ai_classifications,
)
from app.services.ai.background import (
    process_complaint_classification,
)


logger = logging.getLogger(__name__)


def recover_stale_classifications():
    try:
        with get_db_connection() as db:
            recovered_complaints = recover_stale_ai_classifications(
                db=db,
                stale_after_seconds=AI_RECOVERY_STALE_AFTER_SECONDS,
                batch_size=AI_RECOVERY_BATCH_SIZE,
            )

        if not recovered_complaints:
            return

        def process_recovered_complaint(complaint):
            complaint_id, title, description, attempt_id = complaint

            logger.warning(
                "Recovering AI classification for complaint %s.",
                complaint_id,
            )

            process_complaint_classification(
                complaint_id=complaint_id,
                title=title,
                description=description,
                attempt_id=attempt_id,
            )

        with ThreadPoolExecutor(
            max_workers=min(
                len(recovered_complaints),
                AI_RECOVERY_BATCH_SIZE,
            )
        ) as executor:
            list(
                executor.map(
                    process_recovered_complaint,
                    recovered_complaints,
                )
            )

        logger.info(
            "Processed %s recovered AI classification attempts.",
            len(recovered_complaints),
        )

    except Exception:
        logger.exception(
            "AI classification recovery cycle failed."
        )
