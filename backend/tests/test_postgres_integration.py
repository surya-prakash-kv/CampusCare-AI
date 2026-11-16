import pytest
from uuid import uuid4

from app.repositories.ai_metrics import get_ai_classification_metrics
from app.repositories.complaint import (
    create_complaint,
    create_complaint_history,
    create_complaint_ai_review,
    get_complaint_history,
    mark_ai_classification_pending,
    recover_stale_ai_classifications,
    update_ai_classification,
)


def create_test_user(db, role="STUDENT"):
    email = f"{uuid4().hex}@campuscare.test"

    with db.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO users (
                full_name, email, password_hash, role
            )
            VALUES (%s, %s, %s, %s)
            RETURNING id;
            """,
            ("Integration Test User", email, "test-hash", role),
        )
        return cursor.fetchone()[0]


def create_test_complaint(db, student_id):
    return create_complaint(
        db=db,
        student_id=student_id,
        title="Integration test complaint",
        description="Testing real PostgreSQL persistence.",
        category="HOSTEL",
    )


def test_complaint_and_history_persist(postgres_connection):
    db = postgres_connection
    student_id = create_test_user(db)
    complaint = create_test_complaint(db, student_id)
    complaint_id = complaint[0]

    create_complaint_history(
        db,
        complaint_id,
        student_id,
        "OPEN",
        remarks="Integration test submission",
    )

    history = get_complaint_history(db, complaint_id)

    assert len(history) == 1
    assert history[0][1] == complaint_id
    assert history[0][2] == student_id
    assert history[0][4] == "OPEN"


def test_ai_classification_attempt_and_stale_recovery(
    postgres_connection,
):
    db = postgres_connection
    student_id = create_test_user(db)
    complaint = create_test_complaint(db, student_id)
    complaint_id = complaint[0]

    attempt_id = mark_ai_classification_pending(db, complaint_id)

    assert attempt_id is not None

    with db.cursor() as cursor:
        cursor.execute(
            """
            UPDATE complaints
            SET ai_classification_started_at =
                CURRENT_TIMESTAMP - INTERVAL '10 minutes'
            WHERE id = %s;
            """,
            (complaint_id,),
        )

    recovered = recover_stale_ai_classifications(
        db,
        stale_after_seconds=120,
        batch_size=10,
    )

    assert len(recovered) == 1
    assert recovered[0][0] == complaint_id
    assert recovered[0][3] != attempt_id
    assert recovered[0][3] is not None

    assert update_ai_classification(
        db,
        complaint_id,
        attempt_id,
        "HOSTEL",
        "HIGH",
        0.95,
        "Test classification",
        "integration-test-model",
    ) is False

    assert update_ai_classification(
        db,
        complaint_id,
        recovered[0][3],
        "HOSTEL",
        "HIGH",
        0.95,
        "Test classification",
        "integration-test-model",
    ) is True


def test_ai_review_persists(postgres_connection):
    db = postgres_connection
    student_id = create_test_user(db)
    admin_id = create_test_user(db, role="ADMIN")
    complaint = create_test_complaint(db, student_id)

    review = create_complaint_ai_review(
        db=db,
        complaint_id=complaint[0],
        reviewed_by=admin_id,
        decision="ACCEPTED",
        ai_suggested_category="HOSTEL",
        ai_suggested_priority="HIGH",
        ai_confidence=0.95,
        ai_model="integration-test-model",
        original_category="HOSTEL",
        original_priority="MEDIUM",
        final_category="HOSTEL",
        final_priority="HIGH",
        remarks="Integration review",
    )

    assert review[0] is not None
    assert review[1] == complaint[0]
    assert review[2] == admin_id
    assert review[3] == "ACCEPTED"


def test_ai_metrics_reflect_database_records(postgres_connection):
    db = postgres_connection
    student_id = create_test_user(db)
    complaint = create_test_complaint(db, student_id)

    attempt_id = mark_ai_classification_pending(
        db,
        complaint[0],
    )
    assert attempt_id is not None

    metrics = get_ai_classification_metrics(db)

    assert metrics["total_complaints"] >= 1
    assert metrics["pending"] >= 1
    assert any(
        item["attempt_count"] == 1 and item["total"] >= 1
        for item in metrics["attempt_distribution"]
    )


def test_database_enforces_invalid_priority(postgres_connection):
    db = postgres_connection
    student_id = create_test_user(db)

    with pytest.raises(Exception):
        with db.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO complaints (
                    student_id, title, description, priority
                )
                VALUES (%s, %s, %s, %s);
                """,
                (
                    student_id,
                    "Invalid priority test",
                    "Testing database constraint.",
                    "INVALID",
                ),
            )
