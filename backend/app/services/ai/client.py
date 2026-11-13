from openai import OpenAI

from app.core.config import OPENAI_API_KEY


def get_openai_client():
    if not OPENAI_API_KEY:
        return None

    return OpenAI(
        api_key=OPENAI_API_KEY,
        timeout=15.0,
        max_retries=1,
    )
