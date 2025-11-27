from __future__ import annotations

try:  # pragma: no cover - optional dependency
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None  # type: ignore

from app.utils.config import Config


def get_openai_client():
    if OpenAI is None or not Config.OPENAI_API_KEY:
        return None
    return OpenAI(api_key=Config.OPENAI_API_KEY)
