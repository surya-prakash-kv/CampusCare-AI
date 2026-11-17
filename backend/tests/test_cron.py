from fastapi.testclient import TestClient

from app.main import create_app


def create_test_client(monkeypatch):
    monkeypatch.setattr(
        "app.main.validate_application_config",
        lambda environment=None: None,
    )
    monkeypatch.setattr(
        "app.main.configure_logging",
        lambda environment=None: None,
    )

    async def fake_recovery_loop():
        import asyncio
        await asyncio.Event().wait()

    monkeypatch.setattr(
        "app.main.ai_recovery_loop",
        fake_recovery_loop,
    )

    return TestClient(
    create_app(
        environment="testing",
        allowed_origins=(),
    ),
    raise_server_exceptions=False,
)


def test_ai_recovery_cron_returns_503_when_secret_is_missing(monkeypatch):
    monkeypatch.setattr("app.api.cron.CRON_SECRET", None)

    with create_test_client(monkeypatch) as client:
        response = client.post("/api/internal/ai-recovery")

    assert response.status_code == 503
    assert response.json()["detail"] == "Cron authentication is not configured"


def test_ai_recovery_cron_rejects_invalid_authorization(monkeypatch):
    monkeypatch.setattr("app.api.cron.CRON_SECRET", "test-secret-with-more-than-32-characters")

    with create_test_client(monkeypatch) as client:
        response = client.post(
            "/api/internal/ai-recovery",
            headers={"Authorization": "Bearer invalid-token"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid cron authorization"


def test_ai_recovery_cron_triggers_recovery_with_valid_authorization(monkeypatch):
    secret = "test-secret-with-more-than-32-characters"
    recovery_mock = __import__("unittest.mock", fromlist=["Mock"]).Mock()

    monkeypatch.setattr("app.api.cron.CRON_SECRET", secret)
    monkeypatch.setattr(
        "app.api.cron.recover_stale_classifications",
        recovery_mock,
    )

    with create_test_client(monkeypatch) as client:
        response = client.post(
            "/api/internal/ai-recovery",
            headers={"Authorization": f"Bearer {secret}"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "status": "completed",
        "operation": "ai-classification-recovery",
    }
    recovery_mock.assert_called_once_with()

def test_ai_recovery_cron_triggers_recovery_with_valid_get_request(monkeypatch):
    secret = "test-secret-with-more-than-32-characters"
    from unittest.mock import Mock

    recovery_mock = Mock()

    monkeypatch.setattr("app.api.cron.CRON_SECRET", secret)
    monkeypatch.setattr(
        "app.api.cron.recover_stale_classifications",
        recovery_mock,
    )

    with create_test_client(monkeypatch) as client:
        response = client.get(
            "/api/internal/ai-recovery",
            headers={"Authorization": f"Bearer {secret}"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    recovery_mock.assert_called_once_with()

def test_ai_recovery_cron_returns_500_when_recovery_fails(monkeypatch):
    secret = "test-secret-with-more-than-32-characters"

    def failing_recovery():
        raise RuntimeError("Database unavailable")

    monkeypatch.setattr("app.api.cron.CRON_SECRET", secret)
    monkeypatch.setattr(
        "app.api.cron.recover_stale_classifications",
        failing_recovery,
    )

    with create_test_client(monkeypatch) as client:
        response = client.get(
            "/api/internal/ai-recovery",
            headers={"Authorization": f"Bearer {secret}"},
        )

    assert response.status_code == 500
