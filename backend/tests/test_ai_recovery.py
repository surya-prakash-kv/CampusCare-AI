
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.main import app, ai_recovery_loop, lifespan
from app.repositories.complaint import (
    recover_stale_ai_classifications,
)


def test_recovery_rejects_invalid_timeout():
    with pytest.raises(ValueError):
        recover_stale_ai_classifications(
            db=MagicMock(),
            stale_after_seconds=0,
        )


def test_recovery_rejects_invalid_batch_size():
    with pytest.raises(ValueError):
        recover_stale_ai_classifications(
            db=MagicMock(),
            batch_size=0,
        )


def test_recovery_marks_exhausted_attempts_failed():
    db = MagicMock()
    cursor = MagicMock()

    db.cursor.return_value.__enter__.return_value = cursor

    recover_stale_ai_classifications(db)

    first_query = cursor.execute.call_args_list[0].args[0]

    assert "ai_classification_attempt_count >= 5" in first_query
    assert "SET ai_classification_status = 'FAILED'" in first_query



def test_recovery_claims_stale_and_failed_attempts_atomically():
    db = MagicMock()
    cursor = MagicMock()

    expected_rows = [
        (101, "WiFi issue", "Hostel WiFi unavailable", "new-attempt-id")
    ]

    cursor.fetchall.return_value = expected_rows
    db.cursor.return_value.__enter__.return_value = cursor

    result = recover_stale_ai_classifications(
        db=db,
        stale_after_seconds=120,
        batch_size=10,
    )

    recovery_query = cursor.execute.call_args_list[1].args[0]

    assert "FOR UPDATE SKIP LOCKED" in recovery_query
    assert "gen_random_uuid()" in recovery_query
    assert "ai_classification_attempt_count + 1" in recovery_query
    assert "ai_classification_status = 'FAILED'" in recovery_query
    assert "ai_classification_status = 'PENDING'" in recovery_query
    assert "ai_classification_attempt_count < 5" in recovery_query

    # Both FAILED and PENDING attempts must respect the stale timeout.
    assert recovery_query.count("ai_classification_started_at <=") == 2

    # Verify both timeout parameters and the batch size.
    assert cursor.execute.call_args_list[1].args[1] == (
    120,
    120,
    10,
    )

    assert result == expected_rows



def test_ai_recovery_loop_runs_recovery_in_thread(
    monkeypatch,
):
    recovery_mock = MagicMock()
    sleep_mock = AsyncMock(
        side_effect=asyncio.CancelledError
    )

    monkeypatch.setattr(
        "app.main.recover_stale_classifications",
        recovery_mock,
    )
    monkeypatch.setattr(
        "app.main.asyncio.sleep",
        sleep_mock,
    )

    async def run_test():
        with pytest.raises(asyncio.CancelledError):
            await ai_recovery_loop()

    asyncio.run(run_test())

    recovery_mock.assert_called_once()
    sleep_mock.assert_awaited_once()



def test_lifespan_starts_and_stops_recovery_scheduler(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.main.validate_application_config",
        lambda: None,
    )

    state = {"cancelled": False}

    async def wait_until_cancelled():
        try:
            state["started"].set()
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            state["cancelled"] = True
            raise

    monkeypatch.setattr(
        "app.main.ai_recovery_loop",
        wait_until_cancelled,
    )

    async def run_lifespan():
        state["started"] = asyncio.Event()

        async with lifespan(app):
            await state["started"].wait()
            assert state["cancelled"] is False

        assert state["cancelled"] is True

    asyncio.run(run_lifespan())
