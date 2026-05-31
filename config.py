import os
from google import genai

ENV_KEY_NAMES = [
    "GOOGLE_API_KEY",
    "GEMINI_API_KEY",
    "GENAI_API_KEY",
    "GENAI_KEY",
    "GENAI_APIKEY",
    "OPENAI_API_KEY",
]


def load_dotenv(path=".env"):
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def get_api_key():
    load_dotenv()
    for key_name in ENV_KEY_NAMES:
        value = os.getenv(key_name)
        if value:
            return value
    return None


def create_client(api_key: str):
    return genai.Client(api_key=api_key)
