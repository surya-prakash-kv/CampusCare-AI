
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import get_current_user


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


def test_student_can_access_own_profile(client):
    app.dependency_overrides[get_current_user] = override_user("STUDENT")

    response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json()["role"] == "STUDENT"


def test_admin_cannot_access_student_profile(client):
    app.dependency_overrides[get_current_user] = override_user("ADMIN")

    response = client.get("/api/auth/me")

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You do not have permission to access this resource"
    )


def test_unauthenticated_user_cannot_access_profile(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
