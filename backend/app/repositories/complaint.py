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
