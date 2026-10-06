"""Local Ollama text generation used when the Gemini quota is unavailable."""
import json
import logging
from typing import Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def generate_text(prompt: str, system: str = "") -> str:
    payload = json.dumps({
        "model": settings.ollama_model,
        "system": system,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }).encode()
    request = Request(
        f"{settings.ollama_base_url.rstrip('/')}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=settings.ollama_timeout_seconds) as response:
            result = json.loads(response.read().decode())
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Ollama is unavailable: {exc}") from exc

    text = result.get("response", "").strip()
    if not text:
        raise RuntimeError("Ollama returned an empty response")
    return text


def extract_json(text: str) -> Optional[dict]:
    text = text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None