import pytest
from starlette.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.db.connection import get_db
from app.main import app, create_app

@pytest.mark.parametrize(
    "environment",
    ["", "dev", "staging", "invalid"],
)
def test_create_app_rejects_invalid_environment(environment):
    with pytest.raises(
        RuntimeError,
        match="APP_ENV",
    ):
        create_app(
            environment=environment,
            allowed_origins=(),
        )

def test_production_disables_api_documentation():
    application = create_app(
        environment="production",
        allowed_origins=(),
    )

    assert application.docs_url is None
    assert application.redoc_url is None
    assert application.openapi_url is None


def test_development_enables_api_documentation():
    application = create_app(
        environment="development",
        allowed_origins=(),
    )

    assert application.docs_url == "/docs"
    assert application.redoc_url == "/redoc"
    assert application.openapi_url == "/openapi.json"


def test_cors_uses_only_explicitly_allowed_origins():
    allowed_origins = (
        "http://localhost:5173",
        "https://campuscare.example.com",
    )

    application = create_app(
        environment="production",
        allowed_origins=allowed_origins,
    )

    cors_middleware = next(
        middleware
        for middleware in application.user_middleware
        if middleware.cls is CORSMiddleware
    )

    assert cors_middleware.kwargs["allow_origins"] == list(
        allowed_origins
    )
    assert cors_middleware.kwargs["allow_credentials"] is True


def test_cors_middleware_is_not_added_without_allowed_origins():
    application = create_app(
        environment="production",
        allowed_origins=(),
    )

    assert not any(
        middleware.cls is CORSMiddleware
        for middleware in application.user_middleware
    )


def test_database_health_returns_healthy_when_database_is_connected():
    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def execute(self, query):
            assert query == "SELECT 1;"

        def fetchone(self):
            return (1,)

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

    app.dependency_overrides[get_db] = lambda: FakeConnection()

    try:
        with TestClient(app) as client:
            response = client.get("/api/health/database")

        assert response.status_code == 200
        assert response.json() == {
            "database": "connected",
            "status": "healthy",
        }
    finally:
        app.dependency_overrides.clear()


def test_database_health_returns_503_when_database_fails():
    class FakeConnection:
        def cursor(self):
            raise RuntimeError("Database unavailable")

    app.dependency_overrides[get_db] = lambda: FakeConnection()

    try:
        with TestClient(app) as client:
            response = client.get("/api/health/database")

        assert response.status_code == 503
        assert response.json() == {
            "detail": {
                "database": "disconnected",
                "status": "unhealthy",
            }
        }
    finally:
        app.dependency_overrides.clear()

def test_ai_recovery_scheduler_starts_and_stops_with_app_lifespan(
    monkeypatch,
):
    import asyncio
    from threading import Event

    started = Event()
    stopped = Event()

    async def fake_recovery_loop():
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            stopped.set()

    monkeypatch.setattr(
        "app.main.validate_application_config",
        lambda environment=None: None,
    )
    monkeypatch.setattr(
        "app.main.configure_logging",
        lambda environment=None: None,
    )
    monkeypatch.setattr(
        "app.main.ai_recovery_loop",
        fake_recovery_loop,
    )

    application = create_app(
        environment="testing",
        allowed_origins=(),
    )

    with TestClient(application):
        assert started.wait(timeout=2)

    assert stopped.wait(timeout=2)

def test_ai_recovery_scheduler_does_not_start_when_startup_validation_fails(
    monkeypatch,
):
    from fastapi.testclient import TestClient
    from unittest.mock import MagicMock

    scheduler_mock = MagicMock()

    monkeypatch.setattr(
        "app.main.validate_application_config",
        lambda environment=None: (_ for _ in ()).throw(
            RuntimeError("Invalid application configuration")
        ),
    )
    monkeypatch.setattr(
        "app.main.configure_logging",
        lambda environment=None: None,
    )
    monkeypatch.setattr(
        "app.main.asyncio.create_task",
        scheduler_mock,
    )

    application = create_app(
        environment="testing",
        allowed_origins=(),
    )

    with pytest.raises(
        RuntimeError,
        match="Invalid application configuration",
    ):
        with TestClient(application):
            pass

    scheduler_mock.assert_not_called()

def test_app_startup_validates_the_environment_passed_to_create_app(
    monkeypatch,
):
    from unittest.mock import MagicMock
    import asyncio

    validation_mock = MagicMock()
    monkeypatch.setattr(
        "app.main.validate_application_config",
        validation_mock,
    )
    monkeypatch.setattr(
        "app.main.configure_logging",
        lambda: None,
    )
    monkeypatch.setattr(
        "app.main.ai_recovery_loop",
        lambda: asyncio.sleep(3600),
    )

    application = create_app(
        environment="testing",
        allowed_origins=(),
    )

    with TestClient(application):
        pass

    validation_mock.assert_called_once_with("testing")
