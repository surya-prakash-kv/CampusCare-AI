
import logging

from fastapi import APIRouter, Depends, HTTPException

from app.db.connection import get_db


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/health",
    tags=["Health"]
)


@router.get("/database")
def check_database_health(db=Depends(get_db)):
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()

        return {
            "database": "connected",
            "status": "healthy"
        }

    except Exception:
        logger.exception("Database health check failed.")

        raise HTTPException(
            status_code=503,
            detail={
                "database": "disconnected",
                "status": "unhealthy"
            }
        )
