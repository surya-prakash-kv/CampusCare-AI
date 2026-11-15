
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.complaints import router as complaints_router
from app.core.config import (
    AI_RECOVERY_INTERVAL_SECONDS,
    validate_application_config,
)
from app.services.ai.recovery import recover_stale_classifications
from app.api.ai_operations import router as ai_operations_router


logger = logging.getLogger(__name__)


async def ai_recovery_loop():
    while True:
        try:
            await asyncio.to_thread(
                recover_stale_classifications
            )
        except Exception:
            logger.exception(
                "Unexpected error in AI recovery scheduler."
            )

        await asyncio.sleep(AI_RECOVERY_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_application_config()

    recovery_task = asyncio.create_task(
        ai_recovery_loop(),
        name="ai-classification-recovery",
    )

    logger.info("AI classification recovery scheduler started.")

    try:
        yield
    finally:
        recovery_task.cancel()

        try:
            await recovery_task
        except asyncio.CancelledError:
            logger.info(
                "AI classification recovery scheduler stopped."
            )


app = FastAPI(
    title="CampusCare AI",
    description="AI-Powered Student Service Management Platform",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
def home():
    return {
        "message": "Welcome to CampusCare AI",
        "status": "Application is running"
    }


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(complaints_router)
app.include_router(ai_operations_router)
