from psycopg import Connection

from app.repositories.complaint import (
    create_complaint,
    create_complaint_history,
    get_complaints_by_student,
    get_complaint_by_id,
    get_all_complaints,
    update_complaint_status,
    get_complaint_history,
    mark_ai_classification_pending,
)

def submit_complaint(
    db: Connection,
    student_id: int,
    title: str,
    description: str,
    category: str | None
):
    with db.transaction():
        complaint = create_complaint(
            db=db,
            student_id=student_id,
            title=title,
            description=description,
            category=category
        )

        create_complaint_history(
            db=db,
            complaint_id=complaint[0],
            changed_by=student_id,
            new_status=complaint[7],
            remarks="Complaint submitted"
        )

        attempt_id = mark_ai_classification_pending(
            db=db,
            complaint_id=complaint[0],
        )

        if attempt_id is None:
            raise RuntimeError(
                "Could not mark complaint for AI classification."
            )

    return complaint, attempt_id



def list_student_complaints(
    db: Connection,
    student_id: int
):
    return get_complaints_by_student(
        db=db,
        student_id=student_id
    )

def get_complaint_details(
    db: Connection,
    complaint_id: int,
    current_user: dict
):
    complaint = get_complaint_by_id(
        db=db,
        complaint_id=complaint_id
    )

    if complaint is None:
        return None

    if (
        current_user["role"] == "STUDENT"
        and complaint[1] != current_user["id"]
    ):
        return None

    return complaint

def list_all_complaints(db: Connection):
    return get_all_complaints(db=db)

def change_complaint_status(
    db: Connection,
    complaint_id: int,
    admin_id: int,
    new_status: str,
    remarks: str | None = None
):
    with db.transaction():
        complaint = get_complaint_by_id(
            db=db,
            complaint_id=complaint_id
        )

        if complaint is None:
            return None

        old_status = complaint[7]

        if old_status == new_status:
            raise ValueError("Complaint already has this status")

        updated_complaint = update_complaint_status(
            db=db,
            complaint_id=complaint_id,
            status=new_status
        )

        create_complaint_history(
            db=db,
            complaint_id=complaint_id,
            changed_by=admin_id,
            old_status=old_status,
            new_status=new_status,
            remarks=remarks
        )

        return updated_complaint

def get_complaint_history_details(
    db: Connection,
    complaint_id: int,
    current_user: dict
):
    complaint = get_complaint_by_id(
        db=db,
        complaint_id=complaint_id
    )

    if complaint is None:
        return None

    if (
        current_user["role"] == "STUDENT"
        and complaint[1] != current_user["id"]
    ):
        return None

    return get_complaint_history(
        db=db,
        complaint_id=complaint_id
    )
