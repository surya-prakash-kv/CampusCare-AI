from unittest.mock import MagicMock

from app.services.ai.schemas import ComplaintClassification
import app.services.ai.background as background


def create_mock_db():
    db = MagicMock()
    context = MagicMock()
    context.__enter__.return_value = db
    return db, context


def test_successful_classification_is_persisted(monkeypatch):
    db, context = create_mock_db()

    classification = ComplaintClassification(
        suggested_category="HOSTEL",
        suggested_priority="HIGH",
        confidence=0.95,
        reason="Hostel WiFi is affecting student access.",
    )

    monkeypatch.setattr(
        background,
        "classify_complaint",
        lambda **kwargs: classification,
    )

    update_mock = MagicMock(return_value=True)

    monkeypatch.setattr(
        background,
        "update_ai_classification",
        update_mock,
    )

    monkeypatch.setattr(
        background,
        "get_db_connection",
        lambda: context,
    )

    background.process_complaint_classification(
        complaint_id=10,
        title="Hostel WiFi issue",
        description="WiFi is not working.",
    )

    update_mock.assert_called_once()

    arguments = update_mock.call_args.kwargs

    assert arguments["db"] is db
    assert arguments["complaint_id"] == 10
    assert arguments["suggested_category"] == "HOSTEL"
    assert arguments["suggested_priority"] == "HIGH"
    assert arguments["confidence"] == 0.95


def test_missing_api_key_marks_classification_skipped(monkeypatch):
    db, context = create_mock_db()

    cursor = MagicMock()
    db.cursor.return_value.__enter__.return_value = cursor

    monkeypatch.setattr(
        background,
        "classify_complaint",
        lambda **kwargs: None,
    )

    monkeypatch.setattr(
        background,
        "get_db_connection",
        lambda: context,
    )

    background.process_complaint_classification(
        complaint_id=11,
        title="Library access issue",
        description="Library portal is unavailable.",
    )

    cursor.execute.assert_called_once()

    sql = cursor.execute.call_args.args[0]

    assert "SET ai_classification_status = 'SKIPPED'" in sql
    assert cursor.execute.call_args.args[1] == (11,)


def test_classification_failure_marks_status_failed(monkeypatch):
    db, context = create_mock_db()

    cursor = MagicMock()
    db.cursor.return_value.__enter__.return_value = cursor

    def raise_classification_error(**kwargs):
        raise RuntimeError("Simulated AI provider failure")

    monkeypatch.setattr(
        background,
        "classify_complaint",
        raise_classification_error,
    )

    monkeypatch.setattr(
        background,
        "get_db_connection",
        lambda: context,
    )

    background.process_complaint_classification(
        complaint_id=12,
        title="Transport issue",
        description="College bus is delayed.",
    )

    cursor.execute.assert_called_once()

    sql = cursor.execute.call_args.args[0]

    assert "SET ai_classification_status = 'FAILED'" in sql
    assert cursor.execute.call_args.args[1] == (12,)

def test_ai_classification_error_marks_status_failed(monkeypatch):
    from app.services.ai.classifier import AIClassificationError

    db, context = create_mock_db()

    cursor = MagicMock()
    db.cursor.return_value.__enter__.return_value = cursor

    def raise_ai_error(**kwargs):
        raise AIClassificationError("OpenAI API request failed")

    monkeypatch.setattr(
        background,
        "classify_complaint",
        raise_ai_error,
    )

    monkeypatch.setattr(
        background,
        "get_db_connection",
        lambda: context,
    )

    background.process_complaint_classification(
        complaint_id=13,
        title="Laboratory system unavailable",
        description="Students cannot access the laboratory system.",
    )

    cursor.execute.assert_called_once()

    sql = cursor.execute.call_args.args[0]

    assert "SET ai_classification_status = 'FAILED'" in sql
    assert cursor.execute.call_args.args[1] == (13,)

def test_unpersisted_classification_logs_warning(monkeypatch, caplog):
    import logging

    db, context = create_mock_db()

    classification = ComplaintClassification(
        suggested_category="HOSTEL",
        suggested_priority="MEDIUM",
        confidence=0.90,
        reason="Hostel facility issue.",
    )

    monkeypatch.setattr(
        background,
        "classify_complaint",
        lambda **kwargs: classification,
    )

    monkeypatch.setattr(
        background,
        "update_ai_classification",
        MagicMock(return_value=False),
    )

    monkeypatch.setattr(
        background,
        "get_db_connection",
        lambda: context,
    )

    with caplog.at_level(logging.WARNING):
        background.process_complaint_classification(
            complaint_id=14,
            title="Hostel facility issue",
            description="Hostel facility is unavailable.",
        )

    assert "AI classification result was not persisted" in caplog.text

def test_database_failure_attempts_to_mark_classification_failed(
    monkeypatch,
    caplog,
):
    import logging

    classification = ComplaintClassification(
        suggested_category="HOSTEL",
        suggested_priority="HIGH",
        confidence=0.90,
        reason="Hostel service disruption.",
    )

    monkeypatch.setattr(
        background,
        "classify_complaint",
        lambda **kwargs: classification,
    )

    update_mock = MagicMock(
        side_effect=RuntimeError("Database persistence failed")
    )

    monkeypatch.setattr(
        background,
        "update_ai_classification",
        update_mock,
    )

    db, context = create_mock_db()
    cursor = MagicMock()
    db.cursor.return_value.__enter__.return_value = cursor

    monkeypatch.setattr(
        background,
        "get_db_connection",
        lambda: context,
    )

    with caplog.at_level(logging.ERROR):
        background.process_complaint_classification(
            complaint_id=15,
            title="Hostel water issue",
            description="Water supply is unavailable.",
        )

    assert update_mock.call_count == 1
    cursor.execute.assert_called_once()

    sql = cursor.execute.call_args.args[0]

    assert "SET ai_classification_status = 'FAILED'" in sql
    assert cursor.execute.call_args.args[1] == (15,)
    assert "Background AI classification failed" in caplog.text