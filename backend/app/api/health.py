from fastapi import APIRouter, HTTPException

from app.db.connection import get_db_connection


router = APIRouter(
    prefix="/api/health",
    tags=["Health"]
)


@router.get("/database")
def check_database_health():
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                cursor.fetchone()

        return {
            "database": "connected",
            "status": "healthy"
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail={
                "database": "disconnected",
                "status": "unhealthy"
            }
        )
