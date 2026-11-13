
from psycopg import Connection

from app.repositories.complaint import (
    get_pending_ai_reviews,
    get_complaint_ai_review_for_update,
    create_complaint_ai_review,
)


def list_pending_ai_reviews(db: Connection):
    return get_pending_ai_reviews(db=db)


def review_complaint_ai_classification(
    db: Connection,
    complaint_id: int,
    admin_id: int,
    decision: str,
    final_category: str | None = None,
    final_priority: str | None = None,
    remarks: str | None = None,
):
    with db.transaction():
        complaint = get_complaint_ai_review_for_update(
            db=db,
            complaint_id=complaint_id,
        )

        if complaint is None:
            return None

        (
            _,
            original_category,
            original_priority,
            ai_suggested_category,
            ai_suggested_priority,
            ai_confidence,
            ai_reason,
            ai_model,
            ai_classification_status,
        ) = complaint

        if ai_classification_status != "COMPLETED":
            raise ValueError(
                "Only completed AI classifications can be reviewed"
            )

        if (
            ai_suggested_category is None
            or ai_suggested_priority is None
            or ai_confidence is None
            or ai_model is None
        ):
            raise ValueError(
                "AI classification result is incomplete"
            )

        if decision == "ACCEPTED":
            resolved_category = ai_suggested_category
            resolved_priority = ai_suggested_priority

        elif decision == "REJECTED":
            resolved_category = original_category
            resolved_priority = original_priority

        elif decision == "MODIFIED":
            if final_category is None or final_priority is None:
                raise ValueError(
                    "Final category and priority are required"
                )

            resolved_category = final_category
            resolved_priority = final_priority

        else:
            raise ValueError("Invalid AI review decision")

        if decision in ("ACCEPTED", "MODIFIED"):
            with db.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE complaints
                    SET
                        category = %s,
                        priority = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                    """,
                    (
                        resolved_category,
                        resolved_priority,
                        complaint_id,
                    ),
                )

                if cursor.rowcount != 1:
                    raise RuntimeError(
                        "Complaint update failed during AI review"
                    )

        review = create_complaint_ai_review(
            db=db,
            complaint_id=complaint_id,
            reviewed_by=admin_id,
            decision=decision,
            ai_suggested_category=ai_suggested_category,
            ai_suggested_priority=ai_suggested_priority,
            ai_confidence=ai_confidence,
            ai_model=ai_model,
            original_category=original_category,
            original_priority=original_priority,
            final_category=resolved_category,
            final_priority=resolved_priority,
            remarks=remarks,
        )

        return review
