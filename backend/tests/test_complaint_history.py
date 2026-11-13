from app.services.complaint import get_complaint_history_details


def test_student_can_view_own_complaint_history(monkeypatch):
    complaint = (1, 1, None, "Title", "Description", "HOSTEL",
                 "MEDIUM", "CLOSED", None, None)

    history = [
        (1, 1, 1, None, "OPEN", "Complaint submitted", None)
    ]

    monkeypatch.setattr(
        "app.services.complaint.get_complaint_by_id",
        lambda db, complaint_id: complaint
    )

    monkeypatch.setattr(
        "app.services.complaint.get_complaint_history",
        lambda db, complaint_id: history
    )

    result = get_complaint_history_details(
        db=None,
        complaint_id=1,
        current_user={"id": 1, "role": "STUDENT"}
    )

    assert result == history


def test_student_cannot_view_another_students_history(monkeypatch):
    complaint = (1, 1, None, "Title", "Description", "HOSTEL",
                 "MEDIUM", "CLOSED", None, None)

    monkeypatch.setattr(
        "app.services.complaint.get_complaint_by_id",
        lambda db, complaint_id: complaint
    )

    result = get_complaint_history_details(
        db=None,
        complaint_id=1,
        current_user={"id": 8, "role": "STUDENT"}
    )

    assert result is None


def test_admin_can_view_any_complaint_history(monkeypatch):
    complaint = (1, 1, None, "Title", "Description", "HOSTEL",
                 "MEDIUM", "CLOSED", None, None)

    history = [
        (1, 1, 1, None, "OPEN", "Complaint submitted", None)
    ]

    monkeypatch.setattr(
        "app.services.complaint.get_complaint_by_id",
        lambda db, complaint_id: complaint
    )

    monkeypatch.setattr(
        "app.services.complaint.get_complaint_history",
        lambda db, complaint_id: history
    )

    result = get_complaint_history_details(
        db=None,
        complaint_id=1,
        current_user={"id": 4, "role": "ADMIN"}
    )

    assert result == history


def test_history_returns_none_for_nonexistent_complaint(monkeypatch):
    monkeypatch.setattr(
        "app.services.complaint.get_complaint_by_id",
        lambda db, complaint_id: None
    )

    result = get_complaint_history_details(
        db=None,
        complaint_id=999,
        current_user={"id": 4, "role": "ADMIN"}
    )

    assert result is None