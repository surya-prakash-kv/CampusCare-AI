
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import get_current_user
from app.db.connection import get_db

from app.repositories.ai_metrics import get_ai_classification_metrics
from app.services.ai.metrics import get_ai_operations_metrics


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
        "role": role
    }


@pytest.fixture
def expected_metrics():
    return {
        "total_complaints": 10,
        "not_started": 2,
        "pending": 1,
        "completed": 5,
        "failed": 1,
        "skipped": 1,
        "oldest_pending_age_seconds": 45,
        "attempt_distribution": [
            {"attempt_count": 0, "total": 2},
            {"attempt_count": 1, "total": 5},
            {"attempt_count": 2, "total": 2},
            {"attempt_count": 3, "total": 1}
        ],
        "processing_status": "DEGRADED"
    }


def test_admin_can_view_ai_operations_metrics(
    client,
    expected_metrics,
    monkeypatch
):
    app.dependency_overrides[get_current_user] = override_user("ADMIN")
    app.dependency_overrides[get_db] = lambda: MagicMock()

    monkeypatch.setattr(
        "app.api.ai_operations.get_ai_operations_metrics",
        lambda db: expected_metrics
    )

    response = client.get(
        "/api/admin/ai-operations/metrics"
    )

    assert response.status_code == 200
    assert response.json() == expected_metrics


def test_student_cannot_view_ai_operations_metrics(client):
    app.dependency_overrides[get_current_user] = override_user("STUDENT")
    app.dependency_overrides[get_db] = lambda: MagicMock()

    response = client.get(
        "/api/admin/ai-operations/metrics"
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You do not have permission to access this resource"
    )


def test_unauthenticated_user_cannot_view_ai_operations_metrics(client):
    app.dependency_overrides[get_db] = lambda: MagicMock()

    response = client.get(
        "/api/admin/ai-operations/metrics"
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_repository_returns_ai_classification_metrics():
    db = MagicMock()
    cursor = MagicMock()

    cursor.fetchone.return_value = (
        10, 2, 1, 5, 1, 1, 45
    )

    cursor.fetchall.return_value = [
        (0, 2),
        (1, 5),
        (2, 2),
        (3, 1)
    ]

    db.cursor.return_value.__enter__.return_value = cursor

    result = get_ai_classification_metrics(db)

    assert result == {
        "total_complaints": 10,
        "not_started": 2,
        "pending": 1,
        "completed": 5,
        "failed": 1,
        "skipped": 1,
        "oldest_pending_age_seconds": 45,
        "attempt_distribution": [
            {"attempt_count": 0, "total": 2},
            {"attempt_count": 1, "total": 5},
            {"attempt_count": 2, "total": 2},
            {"attempt_count": 3, "total": 1}
        ]
    }

    assert cursor.execute.call_count == 2


def test_repository_handles_empty_metrics():
    db = MagicMock()
    cursor = MagicMock()

    cursor.fetchone.return_value = (
        0, 0, 0, 0, 0, 0, 0
    )

    cursor.fetchall.return_value = []

    db.cursor.return_value.__enter__.return_value = cursor

    result = get_ai_classification_metrics(db)

    assert result["total_complaints"] == 0
    assert result["pending"] == 0
    assert result["failed"] == 0
    assert result["oldest_pending_age_seconds"] == 0
    assert result["attempt_distribution"] == []

@pytest.mark.parametrize(
    ("metrics", "expected_status"),
    [
        (
            {
                "total_complaints": 0,
                "not_started": 0,
                "pending": 0,
                "completed": 0,
                "failed": 0,
                "skipped": 0,
                "oldest_pending_age_seconds": 0,
                "attempt_distribution": [],
            },
            "IDLE",
        ),
        (
            {
                "total_complaints": 5,
                "not_started": 2,
                "pending": 0,
                "completed": 3,
                "failed": 0,
                "skipped": 0,
                "oldest_pending_age_seconds": 0,
                "attempt_distribution": [],
            },
            "IDLE",
        ),
        (
            {
                "total_complaints": 5,
                "not_started": 0,
                "pending": 2,
                "completed": 3,
                "failed": 0,
                "skipped": 0,
                "oldest_pending_age_seconds": 30,
                "attempt_distribution": [],
            },
            "PROCESSING",
        ),
        (
            {
                "total_complaints": 5,
                "not_started": 0,
                "pending": 0,
                "completed": 3,
                "failed": 2,
                "skipped": 0,
                "oldest_pending_age_seconds": 0,
                "attempt_distribution": [],
            },
            "DEGRADED",
        ),
        (
            {
                "total_complaints": 5,
                "not_started": 0,
                "pending": 0,
                "completed": 5,
                "failed": 0,
                "skipped": 0,
                "oldest_pending_age_seconds": 0,
                "attempt_distribution": [],
            },
            "HEALTHY",
        ),
    ],
)
def test_processing_status(metrics, expected_status, monkeypatch):
    monkeypatch.setattr(
        "app.services.ai.metrics.get_ai_classification_metrics",
        lambda db: metrics.copy(),
    )

    result = get_ai_operations_metrics(MagicMock())
