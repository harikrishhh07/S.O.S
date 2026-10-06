"""
Smart Location Inference: given an image, identify which SRM KTR campus
building/zone is shown using Gemini vision + landmark reference knowledge.

POST /reports/infer-location  — returns building_hint, zone_hint, confidence
"""
import json
import re
import logging
import os
from typing import Optional
from pydantic import BaseModel

from PIL import Image

from app.core.config import get_settings
from app.core.gemini import generate_with_fallback

logger = logging.getLogger(__name__)
settings = get_settings()

# All known campus buildings (from our Location table)
CAMPUS_BUILDINGS = [
    "Tech Park 1", "Tech Park 2", "IT Park", "iOS Development Centre",
    "Main Block", "University Building", "Library Building", "CRC Block",
    "Kalam Block", "PG Block", "Science & Humanities Block",
    "Electrical Science Block", "Bio Tech Block", "Computer Science Block",
    "Hi Tech Block", "Mechanical Block", "Mechanical A Block", "Mechanical B Block",
    "Mechanical C Block", "Mechanical D Block", "Mechanical E Block",
    "Mechanical Hanger", "Aerospace Hanger", "Automobile Block",
    "Basic Engineering Lab", "Heat Engineering Lab", "Hydraulics Lab Annexure",
    "Chemical Block", "Chemistry Research (MCA & MBA)", "Raman Research Park",
    "Structural & Structural Testing Lab", "Workshop", "B.Arch Block",
    "MBA Block", "MBA Annexure I", "MBA Annexure II", "New MBA Block (Law)",
    "Auditorium", "Student Activity (Performing Arts)",
    "Sannasi Hostel IV", "Sannasi Hostel V", "Sannasi Hostel VI",
    "Sannasi Hostel VII", "Sannasi Hostel VIII",
    "International Hostel", "International Hostel II",
    "Meenakshi Womens Hostel", "New Ladies Hostel A", "New Ladies Hostel B",
    "New Ladies Hostel C", "New Ladies Hostel D", "M.B.A. Hostel",
    "Staff Quarters", "Staff Quarters Block A & B",
    "Principal Residence", "Guest House",
    "Office Building", "Office Annexure", "Estate Office",
    "Post Office Building", "Police Outpost Building",
    "Canteen Building", "MBA Canteen Extension III",
    "New Kitchen F Block", "Men's Hostel IV Kitchen Block II", "Java Green",
]

LOCATION_PROMPT = f"""You are an expert in identifying buildings on the SRM University KTR campus from photographs.

You know every building on campus. Look at this image and identify:
1. Which specific building or area is visible
2. Which part/zone of that building (entrance, corridor, lab floor, rooftop, parking, etc.)

Known SRM KTR buildings (use EXACTLY one of these names if you recognise it):
{', '.join(CAMPUS_BUILDINGS)}

Visual landmarks to help you:
- Tech Park 1 & 2: tall modern buildings with blue/yellow/red facade, large glass windows, multiple floors
- Main Block / University Building: white/cream colonial-style architecture with arches and decorative pillars
- SRM Main Gate: large pink arch structure with "SRM UNIVERSITY" text
- Library Building: rectangular modern building
- Auditorium: large domed/hall structure
- Sannasi Hostels: tall residential blocks (IV is the largest, 5478 sq.m)
- New Ladies Hostels A/B/C/D: newer hostel blocks
- MBA Block: academic block with classrooms
- Canteen Building: food service building, usually near open areas
- Sculpture/Open area: outdoor areas with sculptures, walkways, amphitheatre

Return ONLY this JSON — no markdown, no explanation:
{{
  "building": "<exact building name from list, or null if unrecognisable>",
  "zone": "<specific area: entrance|corridor|lab|classroom|parking|rooftop|stairwell|walkway|lawn|etc>",
  "landmark_clues": "<brief note on what visual cues helped identify it>",
  "confidence": <0.0-1.0>,
  "alternative": "<second most likely building, or null>"
}}
"""


class LocationInferenceResult(BaseModel):
    building: Optional[str] = None
    zone: Optional[str] = None
    landmark_clues: Optional[str] = None
    confidence: float = 0.0
    alternative: Optional[str] = None


def _parse_json(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text).strip()
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            return json.loads(m.group())
    return {}


async def infer_location_from_image(image_path: str) -> LocationInferenceResult:
    """Run Gemini vision on an image to identify the campus building/zone."""
    if not settings.gemini_api_key or not os.path.exists(image_path):
        return LocationInferenceResult()

    try:
        img = Image.open(image_path)
        response = generate_with_fallback([LOCATION_PROMPT, img])
        data = _parse_json(response.text)

        # Validate building name against known list
        if data.get("building") and data["building"] not in CAMPUS_BUILDINGS:
            # Fuzzy match: find closest
            b = data["building"].lower()
            match = next(
                (name for name in CAMPUS_BUILDINGS if b in name.lower() or name.lower() in b),
                None
            )
            data["building"] = match  # None if no match

        return LocationInferenceResult(**{k: data.get(k) for k in LocationInferenceResult.__fields__})

    except Exception as e:
        logger.error(f"Location inference error: {e}")
        return LocationInferenceResult()
