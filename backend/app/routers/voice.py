"""
Voice-to-Report: transcribe an audio clip and extract report fields using Gemini.
POST /voice/transcribe  — multipart audio file
Returns: { transcript, title, description, building_hint, zone_hint, hazard_type }
"""
import os
import tempfile
import logging
import json
import re

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.core.config import get_settings
from app.core.gemini import generate_with_fallback
from app.routers.auth import get_current_user
from app.models import User

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/voice", tags=["voice"])

EXTRACT_PROMPT = """You are a campus hazard report assistant for SRM University KTR.

A student has recorded a voice message describing a campus hazard. The transcript is below.

Extract structured report fields from it and return ONLY valid JSON — no markdown, no extra text.

Known buildings on campus (use these exact names when you can match):
Tech Park 1, Tech Park 2, IT Park, Main Block, University Building, Library Building,
Electrical Science Block, Bio Tech Block, Computer Science Block, Hi Tech Block,
Mechanical Block, Auditorium, Sannasi Hostel IV, New Ladies Hostel A, MBA Block,
CRC Block, Canteen Building, Basic Engineering Lab, Raman Research Park, B.Arch Block,
Kalam Block, Aerospace Hanger, Automobile Block, Chemical Block, iOS Development Centre

Hazard types: waterlogging, lighting_issue, infrastructure_issue, maintenance_issue,
cleanliness_issue, access_issue, exposed_wiring, fire_risk, suspicious_activity, other

Return this JSON:
{
  "transcript": "<exact words spoken>",
  "title": "<short issue title, max 8 words>",
  "description": "<cleaned up full description, 1-2 sentences>",
  "building_hint": "<building name if mentioned, else null>",
  "zone_hint": "<specific area/floor/zone if mentioned, else null>",
  "hazard_type": "<hazard type from list above>",
  "severity_hint": <1-5 or null if unclear>,
  "confidence": <0.0-1.0>
}

Transcript:
"""

TEXT_EXTRACT_PROMPT = """You are a campus hazard report assistant for SRM University KTR.

A student has typed or dictated the following message. Extract structured report fields and return ONLY valid JSON.

Known buildings: Tech Park 1, Tech Park 2, IT Park, Main Block, University Building,
Library Building, Electrical Science Block, Bio Tech Block, Computer Science Block,
Hi Tech Block, Mechanical Block, Auditorium, Sannasi Hostel IV, New Ladies Hostel A,
MBA Block, CRC Block, Canteen Building, Basic Engineering Lab, Raman Research Park,
B.Arch Block, Kalam Block, Aerospace Hanger, Automobile Block, Chemical Block, iOS Development Centre

Hazard types: waterlogging, lighting_issue, infrastructure_issue, maintenance_issue,
cleanliness_issue, access_issue, exposed_wiring, fire_risk, suspicious_activity, other

Return this JSON:
{
  "title": "<short issue title, max 8 words>",
  "description": "<cleaned up full description>",
  "building_hint": "<building name if mentioned, else null>",
  "zone_hint": "<area/floor/zone if mentioned, else null>",
  "hazard_type": "<hazard type>",
  "severity_hint": <1-5 or null>,
  "confidence": <0.0-1.0>
}

Input text:
"""


class VoiceExtractResult(BaseModel):
    transcript: Optional[str] = None
    title: str
    description: str
    building_hint: Optional[str] = None
    zone_hint: Optional[str] = None
    hazard_type: str
    severity_hint: Optional[int] = None
    confidence: float


def _parse_json(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text).strip()
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            return json.loads(m.group())
    raise ValueError("No JSON found in response")


@router.post("/transcribe", response_model=VoiceExtractResult)
async def transcribe_voice(
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Accept an audio file (webm/mp4/wav/ogg), transcribe via Gemini,
    and extract structured report fields.
    """
    if not settings.gemini_api_key:
        raise HTTPException(503, "Gemini API not configured")

    # Save upload to temp file
    suffix = os.path.splitext(audio.filename or "audio.webm")[1] or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    try:
        # Upload the audio file to Gemini Files API
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        audio_file = genai.upload_file(tmp_path, mime_type=audio.content_type or "audio/webm")

        response = generate_with_fallback([
            EXTRACT_PROMPT,
            audio_file,
        ])

        data = _parse_json(response.text)
        return VoiceExtractResult(**data)

    except Exception as e:
        logger.error(f"Voice transcription error: {e}")
        raise HTTPException(500, f"Transcription failed: {str(e)}")
    finally:
        os.unlink(tmp_path)


@router.post("/extract-text", response_model=VoiceExtractResult)
async def extract_from_text(
    payload: dict,
    current_user: User = Depends(get_current_user),
):
    """
    Extract report fields from a plain text message (typed or browser STT result).
    Body: { "text": "..." }
    """
    text = payload.get("text", "").strip()
    if not text:
        raise HTTPException(400, "text is required")

    if not settings.gemini_api_key:
        raise HTTPException(503, "Gemini API not configured")

    try:
        response = generate_with_fallback(TEXT_EXTRACT_PROMPT + text)
        data = _parse_json(response.text)
        data.setdefault("transcript", None)
        return VoiceExtractResult(**data)
    except Exception as e:
        logger.error(f"Text extraction error: {e}")
        raise HTTPException(500, f"Extraction failed: {str(e)}")
