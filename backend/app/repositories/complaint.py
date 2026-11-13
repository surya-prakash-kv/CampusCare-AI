from psycopg import Connection


def create_complaint(
    db: Connection,
    student_id: int,
    title: str,
    description: str,
    category: str | None
):
    with db.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO complaints (
                student_id,
                title,
                description,
                category
            )
            VALUES (%s, %s, %s, %s)
            RETURNING
                id,
                student_id,
                assigned_admin_id,
                title,
                description,
                category,
                priority,
                status,
                created_at,
                updated_at;
            """,
            (
                student_id,
                title,
                description,
                category
            )
        )

        return cursor.fetchone()


def create_complaint_history(
    db: Connection,
    complaint_id: int,
    changed_by: int,
    new_status: str,
    old_status: str | None = None,
    remarks: str | None = None
):
    with db.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO complaint_history (
                complaint_id,
                changed_by,
                old_status,
                new_status,
                remarks
            )
            VALUES (%s, %s, %s, %s, %s);
            """,
            (
                complaint_id,
                changed_by,
                old_status,
                new_status,
                remarks
            )
        )


def get_complaints_by_student(
    db: Connection,
    student_id: int
):
    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                id,
                student_id,
                assigned_admin_id,
                title,
                description,
                category,
                priority,
                status,
                created_at,
                updated_at
            FROM complaints
            WHERE student_id = %s
            ORDER BY created_at DESC, id DESC;
            """,
            (student_id,)
        )

        return cursor.fetchall()

def get_complaint_by_id(
    db: Connection,
    complaint_id: int
):
    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                id,
                student_id,
                assigned_admin_id,
                title,
                description,
                category,
                priority,
                status,
                created_at,
                updated_at
            FROM complaints
            WHERE id = %s;
            """,
            (complaint_id,)
        )

        return cursor.fetchone()

def get_all_complaints(db: Connection):
    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                id,
                student_id,
                assigned_admin_id,
                title,
                description,
                category,
                priority,
                status,
                created_at,
                updated_at
            FROM complaints
            ORDER BY created_at DESC, id DESC;
            """
        )

        return cursor.fetchall()

def update_complaint_status(
    db: Connection,
    complaint_id: int,
    status: str
):
    with db.cursor() as cursor:
        cursor.execute(
            """
            UPDATE complaints
            SET
                status = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING
                id,
                student_id,
                assigned_admin_id,
                title,
                description,
                category,
                priority,
                status,
                created_at,
                updated_at;
            """,
            (status, complaint_id)
        )

        return cursor.fetchone()

def get_complaint_history(
    db: Connection,
    complaint_id: int
):
    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                id,
                complaint_id,
                changed_by,
                old_status,
                new_status,
                remarks,
                created_at
            FROM complaint_history
            WHERE complaint_id = %s
            ORDER BY created_at ASC, id ASC;
            """,
            (complaint_id,)
        )

        return cursor.fetchall()


def mark_ai_classification_pending(
    db: Connection,
    complaint_id: int,
):
    with db.cursor() as cursor:
        cursor.execute(
            """
            UPDATE complaints
            SET ai_classification_status = 'PENDING'
            WHERE id = %s
              AND ai_classification_status IN (
                  'NOT_STARTED',
                  'FAILED'
              );
            """,
            (complaint_id,),
        )

        return cursor.rowcount == 1


def update_ai_classification(
    db: Connection,
    complaint_id: int,
    suggested_category: str,
    suggested_priority: str,
    confidence: float,
    reason: str,
    model: str,
):
    with db.cursor() as cursor:
        cursor.execute(
            """
            UPDATE complaints
            SET
                ai_suggested_category = %s,
                ai_suggested_priority = %s,
                ai_confidence = %s,
                ai_reason = %s,
                ai_classification_status = 'COMPLETED',
                ai_model = %s
            WHERE id = %s
              AND ai_classification_status = 'PENDING';
            """,
            (
                suggested_category,
                suggested_priority,
                confidence,
                reason,
                model,
                complaint_id,
            ),
        )

        return cursor.rowcount == 1


def get_pending_ai_reviews(db: Connection):
    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                id,
                student_id,
                title,
                description,
                category,
                priority,
                ai_suggested_category,
                ai_suggested_priority,
                ai_confidence,
                ai_reason,
                ai_model,
                ai_classification_status,
                created_at
            FROM complaints
            WHERE ai_classification_status = 'COMPLETED'
              AND ai_suggested_category IS NOT NULL
              AND ai_suggested_priority IS NOT NULL
              AND ai_confidence IS NOT NULL
              AND ai_model IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM complaint_ai_reviews r
                  WHERE r.complaint_id = complaints.id
               )
            ORDER BY created_at ASC, id ASC;
            """
        )

        return cursor.fetchall()


def get_complaint_ai_review_for_update(
    db: Connection,
    complaint_id: int,
):
    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                id,
                category,
                priority,
                ai_suggested_category,
                ai_suggested_priority,
                ai_confidence,
                ai_reason,
                ai_model,
                ai_classification_status
            FROM complaints
            WHERE id = %s
            FOR UPDATE;
            """,
            (complaint_id,),
        )

        return cursor.fetchone()


def create_complaint_ai_review(
    db: Connection,
    complaint_id: int,
    reviewed_by: int,
    decision: str,
    ai_suggested_category: str,
    ai_suggested_priority: str,
    ai_confidence: float,
    ai_model: str,
    original_category: str | None,
    original_priority: str,
    final_category: str | None,
    final_priority: str,
    remarks: str | None,
):
    with db.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO complaint_ai_reviews (
                complaint_id,
                reviewed_by,
                decision,
                ai_suggested_category,
                ai_suggested_priority,
                ai_confidence,
                ai_model,
                original_category,
                original_priority,
                final_category,
                final_priority,
                remarks
            )
            VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
            RETURNING
                id,
                complaint_id,
                reviewed_by,
                decision,
                ai_suggested_category,
                ai_suggested_priority,
                ai_confidence,
                ai_model,
                original_category,
                original_priority,
                final_category,
                final_priority,
                remarks,
                reviewed_at;
            """,
            (
                complaint_id,
                reviewed_by,
                decision,
                ai_suggested_category,
                ai_suggested_priority,
                ai_confidence,
                ai_model,
                original_category,
                original_priority,
                final_category,
                final_priority,
                remarks,
            ),
        )

        return cursor.fetchone()


def get_complaint_ai_review_history(
    db: Connection,
    complaint_id: int,
):
    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                id,
                complaint_id,
                reviewed_by,
                decision,
                ai_suggested_category,
                ai_suggested_priority,
                ai_confidence,
                ai_model,
                original_category,
                original_priority,
                final_category,
                final_priority,
                remarks,
                reviewed_at
            FROM complaint_ai_reviews
            WHERE complaint_id = %s
            ORDER BY reviewed_at ASC, id ASC;
            """,
            (complaint_id,),
        )

        return cursor.fetchall()
