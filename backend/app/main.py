
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.complaints import router as complaints_router
from app.api.ai_operations import router as ai_operations_router

from app.core.config import (
    APP_ENV,
    CORS_ALLOWED_ORIGINS,
    AI_RECOVERY_INTERVAL_SECONDS,
    validate_application_config,
)

from app.services.ai.recovery import recover_stale_classifications


logger = logging.getLogger(__name__)


def configure_logging():
    from app.core.config import LOG_LEVEL

    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )


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


def create_app(
    environment: str = APP_ENV,
    allowed_origins: tuple = CORS_ALLOWED_ORIGINS,
) -> FastAPI:

    if environment not in {
        "development",
        "testing",
        "production",
    }:
        raise RuntimeError(
            "APP_ENV must be development, testing, or production"
        )

    is_production = environment == "production"

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        validate_application_config(environment)
        configure_logging()

        recovery_task = asyncio.create_task(
            ai_recovery_loop(),
            name="ai-classification-recovery",
        )

        logger.info(
            "AI classification recovery scheduler started."
        )

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

    application = FastAPI(
        title="CampusCare AI",
        description="AI-Powered Student Service Management Platform",
        version="1.0.0",
        lifespan=lifespan,
        docs_url=None if is_production else "/docs",
        redoc_url=None if is_production else "/redoc",
        openapi_url=None if is_production else "/openapi.json",
    )

    if allowed_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=list(allowed_origins),
            allow_credentials=True,
            allow_methods=[
                "GET",
                "POST",
                "PUT",
                "PATCH",
                "DELETE",
                "OPTIONS",
            ],
            allow_headers=[
                "Authorization",
                "Content-Type",
            ],
        )

    @application.get("/")
    def home():
        return {
            "message": "Welcome to CampusCare AI",
            "status": "Application is running",
        }

    application.include_router(health_router)
    application.include_router(auth_router)
    application.include_router(complaints_router)
    application.include_router(ai_operations_router)

    return application


app = create_app()
