from fastapi import FastAPI

from app.api.health import router as health_router


app = FastAPI(
    title="CampusCare AI",
    description="AI-Powered Student Service Management Platform",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Welcome to CampusCare AI",
        "status": "Application is running"
    }


app.include_router(health_router)
