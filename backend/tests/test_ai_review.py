
import pytest
from pydantic import ValidationError

from app.schemas.ai_review import AIReviewRequest

from fastapi.testclient import TestClient

from app.main import app
from app.core.security import get_current_user

from datetime import datetime, timezone
from unittest.mock import MagicMock, call

from app.services.ai_review import review_complaint_ai_classification

from app.repositories.complaint import get_pending_ai_reviews

from app.db.connection import get_db


def test_modified_review_requires_final_category_and_priority():
    with pytest.raises(ValidationError):
        AIReviewRequest(decision="MODIFIED")


def test_modified_review_accepts_final_values():
    request = AIReviewRequest(
        decision="MODIFIED",
        final_category="HOSTEL",
        final_priority="HIGH",
        remarks="AI priority was too low.",
    )

    assert request.decision == "MODIFIED"
    assert request.final_category == "HOSTEL"
    assert request.final_priority == "HIGH"
    assert request.remarks == "AI priority was too low."


def test_accepted_review_rejects_manual_final_values():
    with pytest.raises(ValidationError):
        AIReviewRequest(
            decision="ACCEPTED",
            final_category="HOSTEL",
            final_priority="HIGH",
        )


def test_rejected_review_rejects_manual_final_values():
    with pytest.raises(ValidationError):
        AIReviewRequest(
            decision="REJECTED",
            final_category="HOSTEL",
        )


def test_review_remarks_are_trimmed():
    request = AIReviewRequest(
        decision="ACCEPTED",
        remarks="  Verified by admin  ",
    )

    assert request.remarks == "Verified by admin"


def test_empty_review_remarks_become_none():
    request = AIReviewRequest(
        decision="REJECTED",
        remarks="   ",
    )

    assert request.remarks is None


@pytest.fixture
def client():
    app.dependency_overrides.clear()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def override_user(role: str):
    return lambda: {
        "id": 1,
        "full_name": "Test User",
        "email": "test@example.com",
        "role": role,
    }


def test_student_cannot_access_pending_ai_reviews(client):
    app.dependency_overrides[get_current_user] = override_user("STUDENT")

    response = client.get(
        "/api/complaints/admin/ai-review/pending"
    )

    assert response.status_code == 403


def test_student_cannot_submit_ai_review(client):
    app.dependency_overrides[get_current_user] = override_user("STUDENT")

    response = client.post(
        "/api/complaints/admin/101/ai-review",
        json={"decision": "ACCEPTED"},
    )

    assert response.status_code == 403


def test_student_cannot_access_ai_review_history(client):
    app.dependency_overrides[get_current_user] = override_user("STUDENT")

    response = client.get(
        "/api/complaints/admin/101/ai-review/history"
    )

    assert response.status_code == 403


def make_completed_complaint():
    return (
        101,
        "HOSTEL",
        "MEDIUM",
        "LIBRARY",
        "HIGH",
        0.95,
        "Library portal access issue.",
        "test-model",
        "COMPLETED",
    )


def test_accepted_review_updates_complaint_and_creates_audit():
    db = MagicMock()
    db.transaction.return_value.__enter__.return_value = None

    db.cursor.return_value.__enter__.return_value.rowcount = 1

    from unittest.mock import patch

    with patch(
        "app.services.ai_review.get_complaint_ai_review_for_update",
        return_value=make_completed_complaint(),
    ), patch(
        "app.services.ai_review.create_complaint_ai_review",
        return_value=("audit-record",),
    ) as audit_mock:

        result = review_complaint_ai_classification(
            db=db,
            complaint_id=101,
            admin_id=5,
            decision="ACCEPTED",
        )

    assert result == ("audit-record",)
    db.transaction.assert_called_once()

    audit_mock.assert_called_once()

    assert audit_mock.call_args.kwargs["decision"] == "ACCEPTED"
    assert audit_mock.call_args.kwargs["final_category"] == "LIBRARY"
    assert audit_mock.call_args.kwargs["final_priority"] == "HIGH"


def test_rejected_review_preserves_original_complaint_values():
    db = MagicMock()

    from unittest.mock import patch

    with patch(
        "app.services.ai_review.get_complaint_ai_review_for_update",
        return_value=make_completed_complaint(),
    ), patch(
        "app.services.ai_review.create_complaint_ai_review",
        return_value=("audit-record",),
    ) as audit_mock:

        result = review_complaint_ai_classification(
            db=db,
            complaint_id=101,
            admin_id=5,
            decision="REJECTED",
        )

    assert result == ("audit-record",)

    # Rejection must not update the complaint.
    db.cursor.assert_not_called()

    assert audit_mock.call_args.kwargs["final_category"] == "HOSTEL"
    assert audit_mock.call_args.kwargs["final_priority"] == "MEDIUM"


def test_modified_review_updates_admin_selected_values():
    db = MagicMock()
    db.cursor.return_value.__enter__.return_value.rowcount = 1

    from unittest.mock import patch

    with patch(
        "app.services.ai_review.get_complaint_ai_review_for_update",
        return_value=make_completed_complaint(),
    ), patch(
        "app.services.ai_review.create_complaint_ai_review",
        return_value=("audit-record",),
    ) as audit_mock:

        result = review_complaint_ai_classification(
            db=db,
            complaint_id=101,
            admin_id=5,
            decision="MODIFIED",
            final_category="IT_SUPPORT",
            final_priority="URGENT",
        )

    assert result == ("audit-record",)

    assert audit_mock.call_args.kwargs["final_category"] == "IT_SUPPORT"
    assert audit_mock.call_args.kwargs["final_priority"] == "URGENT"


def test_review_returns_none_when_complaint_does_not_exist():
    db = MagicMock()

    from unittest.mock import patch

    with patch(
        "app.services.ai_review.get_complaint_ai_review_for_update",
        return_value=None,
    ):
        result = review_complaint_ai_classification(
            db=db,
            complaint_id=999,
            admin_id=5,
            decision="ACCEPTED",
        )

    assert result is None


def test_review_rejects_incomplete_ai_classification():
    db = MagicMock()

    incomplete_complaint = (
        101,
        "HOSTEL",
        "MEDIUM",
        None,
        None,
        None,
        None,
        None,
        "COMPLETED",
    )

    from unittest.mock import patch

    with patch(
        "app.services.ai_review.get_complaint_ai_review_for_update",
        return_value=incomplete_complaint,
    ):
        with pytest.raises(ValueError, match="incomplete"):
            review_complaint_ai_classification(
                db=db,
                complaint_id=101,
                admin_id=5,
                decision="ACCEPTED",
            )


def test_review_rejects_classification_not_completed():
    db = MagicMock()

    complaint = list(make_completed_complaint())
    complaint[8] = "PENDING"

    from unittest.mock import patch

    with patch(
        "app.services.ai_review.get_complaint_ai_review_for_update",
        return_value=tuple(complaint),
    ):
        with pytest.raises(ValueError, match="completed"):
            review_complaint_ai_classification(
                db=db,
                complaint_id=101,
                admin_id=5,
                decision="ACCEPTED",
            )


def test_pending_ai_reviews_excludes_previously_reviewed_complaints():
    db = MagicMock()
    cursor = db.cursor.return_value.__enter__.return_value

    expected_rows = [
        (101, 1, "Hostel WiFi issue"),
    ]
    cursor.fetchall.return_value = expected_rows

    result = get_pending_ai_reviews(db=db)

    assert result == expected_rows

    executed_sql = cursor.execute.call_args.args[0]

    assert "ai_classification_status = 'COMPLETED'" in executed_sql
    assert "NOT EXISTS" in executed_sql
    assert "complaint_ai_reviews" in executed_sql
    assert "r.complaint_id = complaints.id" in executed_sql

    cursor.fetchall.assert_called_once()


def test_admin_can_view_pending_ai_reviews(client, monkeypatch):
    db = MagicMock()
    app.dependency_overrides[get_current_user] = override_user("ADMIN")
    app.dependency_overrides[get_db] = lambda: db

    pending_row = (
        101,
        1,
        "Hostel WiFi issue",
        "WiFi is unavailable.",
        "HOSTEL",
        "MEDIUM",
        "HOSTEL",
        "HIGH",
        0.95,
        "Network unavailable.",
        "test-model",
        "COMPLETED",
        datetime.now(timezone.utc),
    )

    monkeypatch.setattr(
        "app.api.complaints.list_pending_ai_reviews",
        lambda **kwargs: [pending_row],
    )

    response = client.get(
        "/api/complaints/admin/ai-review/pending"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["ai_suggested_priority"] == "HIGH"


def test_admin_can_submit_ai_review(client, monkeypatch):
    db = MagicMock()
    app.dependency_overrides[get_current_user] = override_user("ADMIN")
    app.dependency_overrides[get_db] = lambda: db

    review_row = (
        1, 101, 5, "ACCEPTED",
        "HOSTEL", "HIGH", 0.95, "test-model",
        "HOSTEL", "MEDIUM", "HOSTEL", "HIGH",
        "Verified by admin.", datetime.now(timezone.utc),
    )

    review_mock = MagicMock(return_value=review_row)

    monkeypatch.setattr(
        "app.api.complaints.review_complaint_ai_classification",
        review_mock,
    )

    response = client.post(
        "/api/complaints/admin/101/ai-review",
        json={
            "decision": "ACCEPTED",
            "remarks": "Verified by admin.",
        },
    )

    assert response.status_code == 201
    assert response.json()["decision"] == "ACCEPTED"
    assert response.json()["final_priority"] == "HIGH"

    review_mock.assert_called_once()


def test_admin_can_view_ai_review_history(client, monkeypatch):
    db = MagicMock()
    app.dependency_overrides[get_current_user] = override_user("ADMIN")
    app.dependency_overrides[get_db] = lambda: db

    history_row = (
        1, 101, 5, "ACCEPTED",
        "HOSTEL", "HIGH", 0.95, "test-model",
        "HOSTEL", "MEDIUM", "HOSTEL", "HIGH",
        "Verified by admin.", datetime.now(timezone.utc),
    )

    monkeypatch.setattr(
        "app.api.complaints.get_complaint_ai_review_history",
        lambda **kwargs: [history_row],
    )

    response = client.get(
        "/api/complaints/admin/101/ai-review/history"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["decision"] == "ACCEPTED"
