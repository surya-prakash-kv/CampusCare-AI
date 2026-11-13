from fastapi import APIRouter, Depends, status, HTTPException
from psycopg import Connection

from app.core.security import require_role
from app.db.connection import get_db
from app.schemas.complaint import (
    ComplaintCreateRequest,
    ComplaintResponse,
    ComplaintStatusUpdateRequest,
    ComplaintHistoryResponse
)
from app.services.complaint import (
    submit_complaint,
    list_student_complaints,
    get_complaint_details,
    list_all_complaints,
    change_complaint_status,
    get_complaint_history_details
)


router = APIRouter(
    prefix="/api/complaints",
    tags=["Complaints"]
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ComplaintResponse
)
def create_student_complaint(
    complaint_data: ComplaintCreateRequest,
    db: Connection = Depends(get_db),
    current_user: dict = Depends(require_role("STUDENT"))
):
    complaint = submit_complaint(
        db=db,
        student_id=current_user["id"],
        title=complaint_data.title,
        description=complaint_data.description,
        category=complaint_data.category
    )

    return {
        "id": complaint[0],
        "student_id": complaint[1],
        "assigned_admin_id": complaint[2],
        "title": complaint[3],
        "description": complaint[4],
        "category": complaint[5],
        "priority": complaint[6],
        "status": complaint[7],
        "created_at": complaint[8],
        "updated_at": complaint[9]
    }

@router.get(
    "/my",
    response_model=list[ComplaintResponse]
)
def read_my_complaints(
    db: Connection = Depends(get_db),
    current_user: dict = Depends(require_role("STUDENT"))
):
    complaints = list_student_complaints(
        db=db,
        student_id=current_user["id"]
    )

    return [
        {
            "id": complaint[0],
            "student_id": complaint[1],
            "assigned_admin_id": complaint[2],
            "title": complaint[3],
            "description": complaint[4],
            "category": complaint[5],
            "priority": complaint[6],
            "status": complaint[7],
            "created_at": complaint[8],
            "updated_at": complaint[9]
        }
        for complaint in complaints
    ]

@router.get(
    "/{complaint_id}",
    response_model=ComplaintResponse
)
def read_complaint_details(
    complaint_id: int,
    db: Connection = Depends(get_db),
    current_user: dict = Depends(
        require_role("STUDENT", "ADMIN")
    )
):
    complaint = get_complaint_details(
        db=db,
        complaint_id=complaint_id,
        current_user=current_user
    )

    if complaint is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    return {
        "id": complaint[0],
        "student_id": complaint[1],
        "assigned_admin_id": complaint[2],
        "title": complaint[3],
        "description": complaint[4],
        "category": complaint[5],
        "priority": complaint[6],
        "status": complaint[7],
        "created_at": complaint[8],
        "updated_at": complaint[9]
    }

@router.get(
    "/admin/all",
    response_model=list[ComplaintResponse]
)
def read_all_complaints(
    db: Connection = Depends(get_db),
    current_user: dict = Depends(require_role("ADMIN"))
):
    complaints = list_all_complaints(db=db)

    return [
        {
            "id": complaint[0],
            "student_id": complaint[1],
            "assigned_admin_id": complaint[2],
            "title": complaint[3],
            "description": complaint[4],
            "category": complaint[5],
            "priority": complaint[6],
            "status": complaint[7],
            "created_at": complaint[8],
            "updated_at": complaint[9]
        }
        for complaint in complaints
    ]

@router.patch(
    "/admin/{complaint_id}/status",
    response_model=ComplaintResponse
)
def update_status(
    complaint_id: int,
    status_data: ComplaintStatusUpdateRequest,
    db: Connection = Depends(get_db),
    current_user: dict = Depends(require_role("ADMIN"))
):
    try:
        complaint = change_complaint_status(
            db=db,
            complaint_id=complaint_id,
            admin_id=current_user["id"],
            new_status=status_data.status,
            remarks=status_data.remarks
        )
    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error)
        )

    if complaint is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    return {
        "id": complaint[0],
        "student_id": complaint[1],
        "assigned_admin_id": complaint[2],
        "title": complaint[3],
        "description": complaint[4],
        "category": complaint[5],
        "priority": complaint[6],
        "status": complaint[7],
        "created_at": complaint[8],
        "updated_at": complaint[9]
    }

@router.get(
    "/{complaint_id}/history",
    response_model=list[ComplaintHistoryResponse]
)
def get_history(
    complaint_id: int,
    db: Connection = Depends(get_db),
    current_user: dict = Depends(
        require_role("STUDENT", "ADMIN")
    )
):
    history = get_complaint_history_details(
        db=db,
        complaint_id=complaint_id,
        current_user=current_user
    )

    if history is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    return [
        {
            "id": row[0],
            "complaint_id": row[1],
            "changed_by": row[2],
            "old_status": row[3],
            "new_status": row[4],
            "remarks": row[5],
            "created_at": row[6]
        }
        for row in history
    ]