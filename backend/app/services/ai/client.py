from google import genai

from app.core.config import GEMINI_API_KEY


def get_gemini_client():
    if not GEMINI_API_KEY:
        return None

    return genai.Client(
        api_key=GEMINI_API_KEY,
        http_options={
            "timeout": 15000,
            "retry_options": {
                "attempts": 2,
            },
        },
    )
