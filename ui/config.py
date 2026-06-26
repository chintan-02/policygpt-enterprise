import os


BACKEND_BASE_URL = os.getenv("POLICYGPT_BACKEND_URL", "http://localhost:8000")
API_PREFIX = os.getenv("POLICYGPT_API_PREFIX", "/api/v1")
API_TIMEOUT_SECONDS = float(os.getenv("POLICYGPT_API_TIMEOUT_SECONDS", "30"))


def build_api_url(path: str) -> str:
    clean_base = BACKEND_BASE_URL.rstrip("/")
    clean_prefix = API_PREFIX.strip("/")

    if not path.startswith("/"):
        path = f"/{path}"

    return f"{clean_base}/{clean_prefix}{path}"