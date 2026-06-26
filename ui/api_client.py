from __future__ import annotations

import time
from typing import Any

import requests

from ui.config import API_TIMEOUT_SECONDS, build_api_url


class PolicyGPTAPIError(Exception):
    """Raised when the PolicyGPT backend request fails."""


def _extract_error_message(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text or "Backend request failed."

    if isinstance(payload, dict):
        error = payload.get("error")

        if isinstance(error, dict):
            return str(error.get("message") or error.get("code") or payload)

        detail = payload.get("detail")

        if detail:
            return str(detail)

    return str(payload)


def _request(
    method: str,
    path: str,
    **kwargs: Any,
) -> tuple[dict[str, Any], float]:
    url = build_api_url(path)
    start_time = time.perf_counter()

    try:
        response = requests.request(
            method=method,
            url=url,
            timeout=API_TIMEOUT_SECONDS,
            **kwargs,
        )
    except requests.RequestException as exc:
        raise PolicyGPTAPIError(
            "Could not connect to the PolicyGPT backend. "
            "Make sure FastAPI is running on http://localhost:8000."
        ) from exc

    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

    if not response.ok:
        raise PolicyGPTAPIError(_extract_error_message(response))

    try:
        data = response.json()
    except ValueError as exc:
        raise PolicyGPTAPIError("Backend returned a non-JSON response.") from exc

    if not isinstance(data, dict):
        raise PolicyGPTAPIError("Backend returned an unexpected response format.")

    return data, latency_ms


def get_backend_health() -> dict[str, Any]:
    try:
        data, latency_ms = _request("GET", "/health")
        return {
            "healthy": True,
            "data": data,
            "latency_ms": latency_ms,
            "message": "Backend connected",
        }
    except PolicyGPTAPIError as first_error:
        try:
            data, latency_ms = _request("GET", "/ready")
            return {
                "healthy": True,
                "data": data,
                "latency_ms": latency_ms,
                "message": "Backend connected",
            }
        except PolicyGPTAPIError:
            return {
                "healthy": False,
                "data": {},
                "latency_ms": None,
                "message": str(first_error),
            }


def upload_document(
    filename: str,
    file_bytes: bytes,
) -> tuple[dict[str, Any], float]:
    files = {
        "file": (
            filename,
            file_bytes,
            "application/pdf",
        )
    }

    return _request("POST", "/documents/upload", files=files)


def ask_question(
    question: str,
    top_k: int = 5,
) -> tuple[dict[str, Any], float]:
    payload = {
        "question": question,
        "top_k": top_k,
    }

    return _request("POST", "/documents/ask", json=payload)


def retrieve_evidence(
    query: str,
    top_k: int = 5,
) -> tuple[dict[str, Any], float]:
    payload = {
        "query": query,
        "top_k": top_k,
    }

    return _request("POST", "/documents/evidence", json=payload)