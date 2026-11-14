
from datetime import datetime, timezone
from unittest.mock import MagicMock

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
    )

    submit_mock = MagicMock(return_value=complaint)
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

    submit_mock.assert_called_once()

    background_mock.assert_called_once_with(
        complaint_id=101,
        title="Hostel WiFi not working",
        description="Students cannot access hostel WiFi.",
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
    )

    monkeypatch.setattr(
        "app.api.complaints.submit_complaint",
        lambda **kwargs: complaint,
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
