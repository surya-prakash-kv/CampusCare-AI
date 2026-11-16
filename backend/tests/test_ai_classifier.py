from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from google.genai import errors
from pydantic import ValidationError

import app.services.ai.classifier as classifier
from app.services.ai.schemas import ComplaintClassification


def test_classification_skipped_when_api_key_is_missing(monkeypatch):
    monkeypatch.setattr(
        classifier,
        "get_gemini_client",
        lambda: None,
    )

    result = classifier.classify_complaint(
        title="Hostel WiFi not working",
        description="Students cannot access the hostel WiFi.",
    )

    assert result is None


def test_classification_returns_structured_result(monkeypatch):
    expected = ComplaintClassification(
        suggested_category="HOSTEL",
        suggested_priority="MEDIUM",
        confidence=0.95,
        reason="The complaint describes a hostel WiFi issue.",
    )

    generate_mock = Mock(
        return_value=SimpleNamespace(parsed=expected)
    )

    fake_client = SimpleNamespace(
        models=SimpleNamespace(
            generate_content=generate_mock
        )
    )

    monkeypatch.setattr(
        classifier,
        "get_gemini_client",
        lambda: fake_client,
    )

    result = classifier.classify_complaint(
        title="Hostel WiFi not working",
        description="Students cannot access the hostel WiFi.",
    )

    assert result == expected
    generate_mock.assert_called_once()

    call_arguments = generate_mock.call_args.kwargs

    assert call_arguments["model"] == classifier.GEMINI_MODEL
    assert call_arguments["config"]["response_mime_type"] == "application/json"
    assert (
        call_arguments["config"]["response_schema"]
        is ComplaintClassification
    )
    assert "Hostel WiFi not working" in call_arguments["contents"]


def test_gemini_failure_raises_classification_error(monkeypatch):
    generate_mock = Mock(
        side_effect=errors.APIError(
            500,
            {"error": "Simulated API failure"},
        )
    )

    fake_client = SimpleNamespace(
        models=SimpleNamespace(
            generate_content=generate_mock
        )
    )

    monkeypatch.setattr(
        classifier,
        "get_gemini_client",
        lambda: fake_client,
    )

    with pytest.raises(classifier.AIClassificationError):
        classifier.classify_complaint(
            title="Hostel WiFi not working",
            description="Students cannot access the hostel WiFi.",
        )


def test_classification_fails_when_parsed_output_is_missing(monkeypatch):
    fake_client = SimpleNamespace(
        models=SimpleNamespace(
            generate_content=Mock(
                return_value=SimpleNamespace(parsed=None)
            )
        )
    )

    monkeypatch.setattr(
        classifier,
        "get_gemini_client",
        lambda: fake_client,
    )

    with pytest.raises(classifier.AIClassificationError):
        classifier.classify_complaint(
            title="Hostel WiFi not working",
            description="Students cannot access the hostel WiFi.",
        )


def test_invalid_structured_response_raises_validation_error():
    with pytest.raises(ValidationError):
        ComplaintClassification(
            suggested_category="INVALID_CATEGORY",
            suggested_priority="MEDIUM",
            confidence=0.95,
            reason="Invalid category test.",
        )
