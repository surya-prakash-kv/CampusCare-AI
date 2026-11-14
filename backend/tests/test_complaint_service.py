from unittest.mock import MagicMock

import pytest

from app.services.complaint import (
    change_complaint_status,
    submit_complaint,
)
from uuid import uuid4


@pytest.fixture
def db():
    return MagicMock()

def test_submit_complaint_success(db, monkeypatch):
    complaint = (
        101,
        1,
        None,
        "Hostel WiFi not working",
        "Students cannot access hostel WiFi.",
        "HOSTEL",
        "MEDIUM",
        "OPEN",
        None,
        None,
    )

    create_complaint_mock = MagicMock(return_value=complaint)
    create_history_mock = MagicMock()
    attempt_id = uuid4()
    pending_mock = MagicMock(return_value=attempt_id)

    monkeypatch.setattr(
        "app.services.complaint.create_complaint",
        create_complaint_mock,
    )

    monkeypatch.setattr(
        "app.services.complaint.create_complaint_history",
        create_history_mock,
    )

    monkeypatch.setattr(
        "app.services.complaint.mark_ai_classification_pending",
        pending_mock,
    )

    result = submit_complaint(
        db=db,
        student_id=1,
        title="Hostel WiFi not working",
        description="Students cannot access hostel WiFi.",
        category="HOSTEL",
    )

    assert result == (complaint, attempt_id)

    create_complaint_mock.assert_called_once()
    create_history_mock.assert_called_once_with(
        db=db,
        complaint_id=101,
        changed_by=1,
        new_status="OPEN",
        remarks="Complaint submitted",
    )
    pending_mock.assert_called_once_with(
        db=db,
        complaint_id=101,
    )

    db.transaction.assert_called_once_with()



def test_submit_complaint_rolls_back_when_pending_update_fails(
    db,
    monkeypatch,
):
    complaint = (
        102,
        1,
        None,
        "Transport delay",
        "College bus service is delayed.",
        "TRANSPORT",
        "MEDIUM",
        "OPEN",
        None,
        None,
    )

    create_complaint_mock = MagicMock(return_value=complaint)
    create_history_mock = MagicMock()
    pending_mock = MagicMock(return_value=None)

    monkeypatch.setattr(
        "app.services.complaint.create_complaint",
        create_complaint_mock,
    )

    monkeypatch.setattr(
        "app.services.complaint.create_complaint_history",
        create_history_mock,
    )

    monkeypatch.setattr(
        "app.services.complaint.mark_ai_classification_pending",
        pending_mock,
    )

    with pytest.raises(
        RuntimeError,
        match="Could not mark complaint for AI classification.",
    ):
        submit_complaint(
            db=db,
            student_id=1,
            title="Transport delay",
            description="College bus service is delayed.",
            category="TRANSPORT",
        )

    create_complaint_mock.assert_called_once()
    create_history_mock.assert_called_once()
    pending_mock.assert_called_once()

    db.transaction.assert_called_once_with()



def test_change_complaint_status_uses_row_lock(
    db,
    monkeypatch,
):
    complaint = (
        101,
        1,
        None,
        "Hostel WiFi not working",
        "Students cannot access hostel WiFi.",
        "HOSTEL",
        "MEDIUM",
        "OPEN",
        None,
        None,
    )

    get_locked_complaint_mock = MagicMock(
        return_value=complaint
    )
    update_status_mock = MagicMock(
        return_value=complaint
    )
    create_history_mock = MagicMock()

    monkeypatch.setattr(
        "app.services.complaint.get_complaint_by_id_for_update",
        get_locked_complaint_mock,
    )
    monkeypatch.setattr(
        "app.services.complaint.update_complaint_status",
        update_status_mock,
    )
    monkeypatch.setattr(
        "app.services.complaint.create_complaint_history",
        create_history_mock,
    )

    result = change_complaint_status(
        db=db,
        complaint_id=101,
        admin_id=2,
        new_status="IN_PROGRESS",
        remarks="Investigation started",
    )

    assert result == complaint

    get_locked_complaint_mock.assert_called_once_with(
        db=db,
        complaint_id=101,
    )

    update_status_mock.assert_called_once_with(
        db=db,
        complaint_id=101,
        status="IN_PROGRESS",
    )

    create_history_mock.assert_called_once_with(
        db=db,
        complaint_id=101,
        changed_by=2,
        old_status="OPEN",
        new_status="IN_PROGRESS",
        remarks="Investigation started",
    )

    db.transaction.assert_called_once_with()


def test_change_complaint_status_rejects_same_status(
    db,
    monkeypatch,
):
    complaint = (
        101,
        1,
        None,
        "Hostel WiFi not working",
        "Students cannot access hostel WiFi.",
        "HOSTEL",
        "MEDIUM",
        "OPEN",
        None,
        None,
    )

    get_locked_complaint_mock = MagicMock(
        return_value=complaint
    )
    update_status_mock = MagicMock()
    create_history_mock = MagicMock()

    monkeypatch.setattr(
        "app.services.complaint.get_complaint_by_id_for_update",
        get_locked_complaint_mock,
    )
    monkeypatch.setattr(
        "app.services.complaint.update_complaint_status",
        update_status_mock,
    )
    monkeypatch.setattr(
        "app.services.complaint.create_complaint_history",
        create_history_mock,
    )

    with pytest.raises(
        ValueError,
        match="Complaint already has this status",
    ):
        change_complaint_status(
            db=db,
            complaint_id=101,
            admin_id=2,
            new_status="OPEN",
        )

    get_locked_complaint_mock.assert_called_once()
    update_status_mock.assert_not_called()
    create_history_mock.assert_not_called()

    db.transaction.assert_called_once_with()
