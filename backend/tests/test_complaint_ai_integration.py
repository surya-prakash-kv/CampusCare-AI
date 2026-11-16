
from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import get_current_user
from app.db.connection import get_db


@pytest.fixture
def client():
    app.dependency_overrides.clear()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def override_student():
    return {
        "id": 1,
        "full_name": "Test Student",
        "email": "student@example.com",
        "role": "STUDENT",
    }


def test_complaint_creation_schedules_ai_classification(
    client,
    monkeypatch,
):
    db = MagicMock()
    app.dependency_overrides[get_current_user] = override_student
    app.dependency_overrides[get_db] = lambda: db

    complaint = (
        101,
        1,
        None,
        "Hostel WiFi not working",
        "Students cannot access hostel WiFi.",
        "HOSTEL",
        "MEDIUM",
        "OPEN",
        datetime.now(timezone.utc),
        datetime.now(timezone.utc),
        None, None, None, None, "PENDING", None,
    )

    attempt_id = uuid4()

    submit_mock = MagicMock(
        return_value=(complaint, attempt_id)
    )
    background_mock = MagicMock()

    monkeypatch.setattr(
        "app.api.complaints.submit_complaint",
        submit_mock,
    )

    monkeypatch.setattr(
        "app.api.complaints.process_complaint_classification",
        background_mock,
    )

    response = client.post(
        "/api/complaints",
        json={
            "title": "Hostel WiFi not working",
            "description": "Students cannot access hostel WiFi.",
            "category": "HOSTEL",
        },
    )

    assert response.status_code == 201

    response_data = response.json()

    assert response_data["id"] == 101
    assert response_data["category"] == "HOSTEL"
    assert response_data["priority"] == "MEDIUM"

    # Attempt UUID must not be exposed in the public response.
    assert "attempt_id" not in response_data

    submit_mock.assert_called_once()

    background_mock.assert_called_once_with(
        complaint_id=101,
        title="Hostel WiFi not working",
        description="Students cannot access hostel WiFi.",
        attempt_id=attempt_id,
    )


def test_complaint_creation_adds_ai_background_task(
    client,
    monkeypatch,
):
    db = MagicMock()
    app.dependency_overrides[get_current_user] = override_student
    app.dependency_overrides[get_db] = lambda: db

    complaint = (
        102,
        1,
        None,
        "Library portal unavailable",
        "Students cannot access the library portal.",
        "LIBRARY",
        "MEDIUM",
        "OPEN",
        datetime.now(timezone.utc),
        datetime.now(timezone.utc),
        None, None, None, None, "PENDING", None,
    )

    attempt_id = uuid4()

    monkeypatch.setattr(
        "app.api.complaints.submit_complaint",
        lambda **kwargs: (complaint, attempt_id),
    )

    background_mock = MagicMock()

    monkeypatch.setattr(
        "app.api.complaints.process_complaint_classification",
        background_mock,
    )

    response = client.post(
        "/api/complaints",
        json={
            "title": "Library portal unavailable",
            "description": "Students cannot access the library portal.",
            "category": "LIBRARY",
        },
    )

    assert response.status_code == 201

    background_mock.assert_called_once_with(
        complaint_id=102,
        title="Library portal unavailable",
        description="Students cannot access the library portal.",
        attempt_id=attempt_id,
    )


def test_ai_task_not_scheduled_when_complaint_submission_fails(
    client,
    monkeypatch,
):
    app.dependency_overrides[get_current_user] = override_student

    db = MagicMock()
    app.dependency_overrides[get_db] = lambda: db

    def failed_submission(**kwargs):
        raise RuntimeError(
            "Could not mark complaint for AI classification."
        )

    monkeypatch.setattr(
        "app.api.complaints.submit_complaint",
        failed_submission,
    )

    background_mock = MagicMock()

    monkeypatch.setattr(
        "app.api.complaints.process_complaint_classification",
        background_mock,
    )

    with pytest.raises(RuntimeError):
        client.post(
            "/api/complaints",
            json={
                "title": "Transport delay",
                "description": "College bus service is delayed.",
                "category": "TRANSPORT",
            },
        )

    background_mock.assert_not_called()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("title", "abcd"),
        ("title", "   "),
        ("title", "x" * 201),
        ("description", "short"),
        ("description", "   "),
        ("description", "x" * 5001),
        ("category", "x" * 51),
    ],
)
def test_complaint_creation_rejects_invalid_field_values(
    client,
    monkeypatch,
    field,
    value,
):
    app.dependency_overrides[get_current_user] = override_student
    app.dependency_overrides[get_db] = lambda: MagicMock()

    submit_mock = MagicMock()

    monkeypatch.setattr(
        "app.api.complaints.submit_complaint",
        submit_mock,
    )

    payload = {
        "title": "Hostel WiFi not working",
        "description": "Students cannot access hostel WiFi.",
        "category": "HOSTEL",
    }
    payload[field] = value

    response = client.post(
        "/api/complaints",
        json=payload,
    )

    assert response.status_code == 422
    submit_mock.assert_not_called()


@pytest.mark.parametrize("missing_field", ["title", "description"])
def test_complaint_creation_rejects_missing_required_fields(
    client,
    monkeypatch,
    missing_field,
):
    app.dependency_overrides[get_current_user] = override_student
    app.dependency_overrides[get_db] = lambda: MagicMock()

    submit_mock = MagicMock()

    monkeypatch.setattr(
        "app.api.complaints.submit_complaint",
        submit_mock,
    )

    payload = {
        "title": "Hostel WiFi not working",
        "description": "Students cannot access hostel WiFi.",
        "category": "HOSTEL",
    }
    payload.pop(missing_field)

    response = client.post(
        "/api/complaints",
        json=payload,
    )

    assert response.status_code == 422
    submit_mock.assert_not_called()


@pytest.mark.parametrize(
    "invalid_status",
    [
        "PENDING",
        "INVALID",
        "",
        "open",
    ],
)
def test_complaint_status_update_rejects_invalid_status(
    client,
    monkeypatch,
    invalid_status,
):
    app.dependency_overrides[get_current_user] = lambda: {
        "id": 2,
        "full_name": "Test Admin",
        "email": "admin@example.com",
        "role": "ADMIN",
    }
    app.dependency_overrides[get_db] = lambda: MagicMock()

    update_mock = MagicMock()

    monkeypatch.setattr(
        "app.api.complaints.change_complaint_status",
        update_mock,
    )

    response = client.patch(
        "/api/complaints/admin/101/status",
        json={
            "status": invalid_status,
        },
    )

    assert response.status_code == 422
    update_mock.assert_not_called()


def test_complaint_status_update_rejects_oversized_remarks(
    client,
    monkeypatch,
):
    app.dependency_overrides[get_current_user] = lambda: {
        "id": 2,
        "full_name": "Test Admin",
        "email": "admin@example.com",
        "role": "ADMIN",
    }
    app.dependency_overrides[get_db] = lambda: MagicMock()

    update_mock = MagicMock()

    monkeypatch.setattr(
        "app.api.complaints.change_complaint_status",
        update_mock,
    )

    response = client.patch(
        "/api/complaints/admin/101/status",
        json={
            "status": "IN_PROGRESS",
            "remarks": "x" * 1001,
        },
    )

    assert response.status_code == 422
    update_mock.assert_not_called()


def test_student_cannot_access_all_complaints(client):
    app.dependency_overrides[get_current_user] = override_student
    app.dependency_overrides[get_db] = lambda: MagicMock()

    response = client.get("/api/complaints/admin/all")

    assert response.status_code == 403


def test_admin_cannot_access_student_complaints_endpoint(client):
    app.dependency_overrides[get_current_user] = lambda: {
        "id": 2,
        "full_name": "Test Admin",
        "email": "admin@example.com",
        "role": "ADMIN",
    }
    app.dependency_overrides[get_db] = lambda: MagicMock()

    response = client.get("/api/complaints/my")

    assert response.status_code == 403


def test_student_cannot_update_complaint_status(client):
    app.dependency_overrides[get_current_user] = override_student
    app.dependency_overrides[get_db] = lambda: MagicMock()

    response = client.patch(
        "/api/complaints/admin/101/status",
        json={"status": "IN_PROGRESS"},
    )

    assert response.status_code == 403


def test_student_cannot_view_another_students_complaint_api(
    client,
    monkeypatch,
):
    app.dependency_overrides[get_current_user] = override_student
    app.dependency_overrides[get_db] = lambda: MagicMock()

    another_students_complaint = (
        101, 8, None, "Title", "Description", "HOSTEL",
        "MEDIUM", "OPEN", None, None,
    )

    monkeypatch.setattr(
        "app.services.complaint.get_complaint_by_id",
        lambda db, complaint_id: another_students_complaint,
    )

    response = client.get("/api/complaints/101")

    assert response.status_code == 404
    assert response.json()["detail"] == "Complaint not found"


def test_student_my_complaints_uses_authenticated_student_id(
    client,
    monkeypatch,
):
    db = MagicMock()
    app.dependency_overrides[get_current_user] = override_student
    app.dependency_overrides[get_db] = lambda: db

    complaint = (
        101, 1, None, "Hostel WiFi issue",
        "WiFi is unavailable.", "HOSTEL", "MEDIUM",
        "OPEN", datetime.now(timezone.utc),
        datetime.now(timezone.utc),
        None, None, None, None, "PENDING", None,
    )

    list_mock = MagicMock(return_value=[complaint])

    monkeypatch.setattr(
        "app.api.complaints.list_student_complaints",
        list_mock,
    )

    response = client.get("/api/complaints/my")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["student_id"] == 1

    list_mock.assert_called_once_with(
        db=db,
        student_id=1,
    )
