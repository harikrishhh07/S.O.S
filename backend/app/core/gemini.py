import logging

import google.generativeai as genai

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

GEMINI_MODEL_CANDIDATES = (
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-flash-latest",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-2.5-flash",
)


def configure_gemini() -> None:
    if settings.gemini_api_key:
        genai.configure(api_key=settings.gemini_api_key)


def _is_model_compatibility_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return (
        "not found" in message
        or "unsupported" in message
        or "is not supported" in message
        or "404" in message
    )


def generate_with_fallback(*parts):
    """Try a small set of Gemini model names and fail over gracefully."""
    if not settings.gemini_api_key:
        raise ValueError("Gemini API not configured")

    configure_gemini()
    payload = []
    for part in parts:
        if part is None:
            continue
        if isinstance(part, (list, tuple)):
            payload.extend(part)
        else:
            payload.append(part)

    last_error = None
    for model_name in GEMINI_MODEL_CANDIDATES:
        try:
            model = genai.GenerativeModel(model_name)
            return model.generate_content(payload)
        except Exception as exc:  # pragma: no cover - exercised through runtime API compatibility
            last_error = exc
            logger.warning("Gemini model %s failed: %s", model_name, exc)
            if not _is_model_compatibility_error(exc):
                raise

    if last_error is not None:
        raise last_error
    raise ValueError("No Gemini model available")