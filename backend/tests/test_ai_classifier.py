from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

import app.services.ai.classifier as classifier
from app.services.ai.schemas import ComplaintClassification


def test_classification_skipped_when_api_key_is_missing(monkeypatch):
    monkeypatch.setattr(
        classifier,
        "get_openai_client",
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

    parse_mock = Mock(
        return_value=SimpleNamespace(
            output_parsed=expected
        )
    )

    fake_client = SimpleNamespace(
        responses=SimpleNamespace(
            parse=parse_mock
        )
    )

    monkeypatch.setattr(
        classifier,
        "get_openai_client",
        lambda: fake_client,
    )

    result = classifier.classify_complaint(
        title="Hostel WiFi not working",
        description="Students cannot access the hostel WiFi.",
    )

    assert result == expected

    parse_mock.assert_called_once()

    call_arguments = parse_mock.call_args.kwargs

    assert call_arguments["model"] == classifier.OPENAI_MODEL
    assert call_arguments["text_format"] is ComplaintClassification
    assert len(call_arguments["input"]) == 2

def test_openai_failure_raises_classification_error(monkeypatch):
    fake_client = SimpleNamespace(
        responses=SimpleNamespace(
            parse=Mock(
                side_effect=classifier.OpenAIError(
                    "Simulated API failure"
                )
            )
        )
    )

    monkeypatch.setattr(
        classifier,
        "get_openai_client",
        lambda: fake_client,
    )

    with pytest.raises(classifier.AIClassificationError):
        classifier.classify_complaint(
            title="Hostel WiFi not working",
            description="Students cannot access the hostel WiFi.",
        )

def test_classification_fails_when_parsed_output_is_missing(monkeypatch):
    fake_client = SimpleNamespace(
        responses=SimpleNamespace(
            parse=Mock(
                return_value=SimpleNamespace(
                    output_parsed=None
                )
            )
        )
    )

    monkeypatch.setattr(
        classifier,
        "get_openai_client",
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