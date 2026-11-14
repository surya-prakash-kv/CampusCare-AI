from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    status,
    HTTPException,
)
from psycopg import Connection

from app.core.security import require_role
from app.db.connection import get_db
from app.repositories.complaint import (
    mark_ai_classification_pending,
)
from app.schemas.complaint import (
    ComplaintCreateRequest,
    ComplaintResponse,
    ComplaintStatusUpdateRequest,
    ComplaintHistoryResponse,
)
from app.schemas.ai_review import (
    AIReviewRequest,
    AIReviewResponse,
    PendingAIReviewResponse,
)
from app.services.ai.background import (
    process_complaint_classification,
)
from app.services.complaint import (
    submit_complaint,
    list_student_complaints,
    get_complaint_details,
    list_all_complaints,
    change_complaint_status,
    get_complaint_history_details,
)
from app.services.ai_review import (
    list_pending_ai_reviews,
    review_complaint_ai_classification,
)
from app.repositories.complaint import (
    mark_ai_classification_pending,
    get_complaint_ai_review_history,
)


router = APIRouter(
    prefix="/api/complaints",
    tags=["Complaints"],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ComplaintResponse,
)
def create_student_complaint(
    complaint_data: ComplaintCreateRequest,
    background_tasks: BackgroundTasks,
    db: Connection = Depends(get_db),
    current_user: dict = Depends(require_role("STUDENT")),
):
    complaint = submit_complaint(
        db=db,
        student_id=current_user["id"],
        title=complaint_data.title,
        description=complaint_data.description,
        category=complaint_data.category,
    )

    background_tasks.add_task(
    process_complaint_classification,
    complaint_id=complaint[0],
    title=complaint[3],
    description=complaint[4]
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
        "updated_at": complaint[9],
    }


@router.get(
    "/my",
    response_model=list[ComplaintResponse],
)
def read_my_complaints(
    db: Connection = Depends(get_db),
    current_user: dict = Depends(require_role("STUDENT")),
):
    complaints = list_student_complaints(
        db=db,
        student_id=current_user["id"],
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
            "updated_at": complaint[9],
        }
        for complaint in complaints
    ]


@router.get(
    "/{complaint_id}",
    response_model=ComplaintResponse,
)
def read_complaint_details(
    complaint_id: int,
    db: Connection = Depends(get_db),
    current_user: dict = Depends(
        require_role("STUDENT", "ADMIN")
    ),
):
    complaint = get_complaint_details(
        db=db,
        complaint_id=complaint_id,
        current_user=current_user,
    )

    if complaint is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found",
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
        "updated_at": complaint[9],
    }


@router.get(
    "/admin/all",
    response_model=list[ComplaintResponse],
)
def read_all_complaints(
    db: Connection = Depends(get_db),
    current_user: dict = Depends(require_role("ADMIN")),
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
            "updated_at": complaint[9],
        }
        for complaint in complaints
    ]


@router.patch(
    "/admin/{complaint_id}/status",
    response_model=ComplaintResponse,
)
def update_status(
    complaint_id: int,
    status_data: ComplaintStatusUpdateRequest,
    db: Connection = Depends(get_db),
    current_user: dict = Depends(require_role("ADMIN")),
):
    try:
        complaint = change_complaint_status(
            db=db,
            complaint_id=complaint_id,
            admin_id=current_user["id"],
            new_status=status_data.status,
            remarks=status_data.remarks,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    if complaint is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found",
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
        "updated_at": complaint[9],
    }


@router.get(
    "/{complaint_id}/history",
    response_model=list[ComplaintHistoryResponse],
)
def get_history(
    complaint_id: int,
    db: Connection = Depends(get_db),
    current_user: dict = Depends(
        require_role("STUDENT", "ADMIN")
    ),
):
    history = get_complaint_history_details(
        db=db,
        complaint_id=complaint_id,
        current_user=current_user,
    )

    if history is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found",
        )

    return [
        {
            "id": row[0],
            "complaint_id": row[1],
            "changed_by": row[2],
            "old_status": row[3],
            "new_status": row[4],
            "remarks": row[5],
            "created_at": row[6],
        }
        for row in history
    ]


@router.get(
    "/admin/ai-review/pending",
    response_model=list[PendingAIReviewResponse],
)
def read_pending_ai_reviews(
    db: Connection = Depends(get_db),
    current_user: dict = Depends(require_role("ADMIN")),
):
    reviews = list_pending_ai_reviews(db=db)

    return [
        {
            "id": row[0],
            "student_id": row[1],
            "title": row[2],
            "description": row[3],
            "category": row[4],
            "priority": row[5],
            "ai_suggested_category": row[6],
            "ai_suggested_priority": row[7],
            "ai_confidence": row[8],
            "ai_reason": row[9],
            "ai_model": row[10],
            "ai_classification_status": row[11],
            "created_at": row[12],
        }
        for row in reviews
    ]



@router.get(
    "/admin/{complaint_id}/ai-review/history",
    response_model=list[AIReviewResponse],
)
def read_ai_review_history(
    complaint_id: int,
    db: Connection = Depends(get_db),
    current_user: dict = Depends(require_role("ADMIN")),
):
    history = get_complaint_ai_review_history(
        db=db,
        complaint_id=complaint_id,
    )

    return [
        {
            "id": row[0],
            "complaint_id": row[1],
            "reviewed_by": row[2],
            "decision": row[3],
            "ai_suggested_category": row[4],
            "ai_suggested_priority": row[5],
            "ai_confidence": row[6],
            "ai_model": row[7],
            "original_category": row[8],
            "original_priority": row[9],
            "final_category": row[10],
            "final_priority": row[11],
            "remarks": row[12],
            "reviewed_at": row[13],
        }
        for row in history
    ]



@router.post(
    "/admin/{complaint_id}/ai-review",
    response_model=AIReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_ai_review(
    complaint_id: int,
    review_data: AIReviewRequest,
    db: Connection = Depends(get_db),
    current_user: dict = Depends(require_role("ADMIN")),
):
    try:
        review = review_complaint_ai_classification(
            db=db,
            complaint_id=complaint_id,
            admin_id=current_user["id"],
            decision=review_data.decision,
            final_category=review_data.final_category,
            final_priority=review_data.final_priority,
            remarks=review_data.remarks,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found",
        )

    return {
        "id": review[0],
        "complaint_id": review[1],
        "reviewed_by": review[2],
        "decision": review[3],
        "ai_suggested_category": review[4],
        "ai_suggested_priority": review[5],
        "ai_confidence": review[6],
        "ai_model": review[7],
        "original_category": review[8],
        "original_priority": review[9],
        "final_category": review[10],
        "final_priority": review[11],
        "remarks": review[12],
        "reviewed_at": review[13],
    }
