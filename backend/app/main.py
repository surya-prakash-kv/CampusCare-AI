from fastapi import FastAPI

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
