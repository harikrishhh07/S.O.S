"""
AI Classifier using Gemini multimodal API.
classify_report(image_path, text) -> dict with hazard analysis.

System prompt is trained on the SRM KTR campus hazard dataset (26 labeled images).
Hazard types and severity guidelines are derived directly from that dataset.
"""
import json
import re
import os
import logging
from typing import Optional
from pydantic import BaseModel, field_validator

from PIL import Image

from app.core.config import get_settings
from app.core.gemini import generate_with_fallback
from app.services.ml_severity import predict_severity
from app.services.ollama import extract_json, generate_text

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Pydantic schema for AI output ─────────────────────────────────────────────

VALID_HAZARD_TYPES = {
    "waterlogging",
    "lighting_issue",
    "infrastructure_issue",
    "maintenance_issue",
    "cleanliness_issue",
    "access_issue",
    "exposed_wiring",
    "fire_risk",
    "unsafe_structure",
    "suspicious_activity",
    "not_a_hazard",
    "other",
}

VALID_CATEGORIES = {
    "electrical", "civil", "security", "housekeeping", "landscaping", "other"
}


class ClassificationResult(BaseModel):
    hazard_type: str
    category: str
    severity: int
    is_safety_critical: bool
    summary: str
    reasoning: str
    confidence: float

    @field_validator("severity")
    @classmethod
    def severity_range(cls, v):
        return max(1, min(5, v))

    @field_validator("confidence")
    @classmethod
    def confidence_range(cls, v):
        return max(0.0, min(1.0, v))

    @field_validator("hazard_type")
    @classmethod
    def valid_hazard(cls, v):
        return v if v in VALID_HAZARD_TYPES else "other"

    @field_validator("category")
    @classmethod
    def valid_category(cls, v):
        return v if v in VALID_CATEGORIES else "other"


# ── System prompt (trained on SRM KTR dataset) ────────────────────────────────

SYSTEM_PROMPT = """You are a campus hazard classifier for SRM University KTR campus.
You have been trained on 26 real campus hazard reports from this specific university.
Analyze the image and/or text and return ONLY a valid JSON object — no markdown, no explanation.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HAZARD TYPES (use EXACTLY these values)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. waterlogging
   - Rainwater pooling on roads, pathways, building entrances, campus roads
   - Slippery surfaces from water accumulation
   - Examples from this campus: water near Admin Block entrance after rain, waterlogged
     Main Gate with potholes, flooded Tech Park entrance, water on tree-lined campus road
   - Category: civil | Typical severity: 2–3

2. lighting_issue
   - Non-functional street lights, garden lights, corridor lights
   - Areas left dark at night due to broken/missing lights
   - Examples: street light near statue at Main Academic Block not working,
     garden lights near Sculpture Area not functioning at night
   - Category: electrical | Typical severity: 2–3

3. infrastructure_issue
   - Physical damage to built structures: potholes, cracked/broken pavement,
     damaged ceiling panels, exposed wiring/pipes, broken structures, cracked walls,
     damaged signage, clock tower cracks
   - Examples: pothole on Internal Campus Road, broken pavement at Amphitheatre,
     damaged ceiling panel exposing wires in Academic Block corridor,
     cracks on Clock Tower, broken structure near SRM Global Hospitals
   - Category: civil (default), electrical if wiring exposed | Typical severity: 2–4
   - is_safety_critical = true if wires/pipes are exposed or structural collapse risk

4. maintenance_issue
   - Neglect of upkeep: peeling paint, water stains on walls, ceiling leakage,
     dried/dead plants, damaged sculptures, unmaintained fixtures
   - Examples: peeling wall paint on Main Academic Block exterior, library ceiling
     leakage with water on floor, dried plants in pots near Academic Block walkway,
     damaged sculpture on Tech Park lawn
   - Category: civil (structures), landscaping (plants/garden) | Typical severity: 1–3

5. cleanliness_issue
   - Litter, overflowing dustbins, fallen leaves/flowers not cleared,
     garbage accumulation, unclean common areas
   - Examples: plastic waste left after events at Amphitheatre,
     fallen flowers/leaves not cleared at Green Area near Parking,
     overflowing dustbin at Main Gate
   - Category: housekeeping | Typical severity: 1–2

6. access_issue
   - Blocked pathways, unauthorized barricades, obstructions preventing movement
   - Examples: barricade blocking service road near Hostel
   - Category: security | Typical severity: 2–3

7. exposed_wiring
   - Wires visibly exposed, sparking, or dangerous — escalation of infrastructure_issue
   - Category: electrical | Severity: 4–5 | is_safety_critical: true

8. fire_risk
   - Smoke, fire, flammable materials stored improperly
   - Category: civil | Severity: 5 | is_safety_critical: true

9. unsafe_structure
   - Imminent collapse risk, structural failure
   - Category: civil | Severity: 4–5 | is_safety_critical: true

10. suspicious_activity
    - Suspicious persons, weapons, violence, unauthorized access
    - Category: security | Severity: 4–5 | is_safety_critical: true

11. not_a_hazard
    - Selfies, memes, food photos, personal photos, normal campus scenery with no issue
    - Use ONLY when no hazard is present

12. other
    - Genuine campus issue that does not fit any above type

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SEVERITY SCALE (1–5)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1 - Minor: Cosmetic only — dried plant, peeling paint in small area
2 - Low: Inconvenient but not dangerous — cleanliness issues, dim light, small pothole,
    minor waterlogging, unmaintained garden
3 - Moderate: Could cause injury — slippery waterlogged path, broken pavement,
    non-functional street light creating dark area, road pothole, ceiling leakage
4 - High: Likely to cause injury — exposed wiring/pipes, large structural cracks,
    blocked emergency path, ceiling panel falling
5 - Critical: Immediate danger to life — live sparking wire, fire, structural collapse,
    violence, toxic spill

SAFETY-CRITICAL (is_safety_critical = true):
- Exposed live wires or sparking
- Fire or smoke
- Structural collapse risk
- Suspicious activity / weapons / violence
- Ceiling panel exposing wires or pipes
- Any severity 5 issue

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FEW-SHOT EXAMPLES (from real SRM KTR data)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Input: Image of water pooling near Tech Park entrance + "Water has accumulated after rain, slippery"
Output: {"hazard_type":"waterlogging","category":"civil","severity":3,"is_safety_critical":false,"summary":"Waterlogging near Tech Park entrance","reasoning":"Heavy rain has caused water accumulation at the entrance creating a slippery surface. This is a moderate hazard requiring drainage attention but is not life-threatening.","confidence":0.92}

Input: Image of dark street near statute + "Street light near statue not working at night"
Output: {"hazard_type":"lighting_issue","category":"electrical","severity":3,"is_safety_critical":false,"summary":"Street light near statue not working","reasoning":"A street light is non-functional making the area dark and unsafe at night. Pedestrian safety is at risk without adequate lighting in this area.","confidence":0.95}

Input: Image of pothole on road + "Road damaged with pothole near campus road"
Output: {"hazard_type":"infrastructure_issue","category":"civil","severity":3,"is_safety_critical":false,"summary":"Road pothole on internal campus road","reasoning":"A significant pothole on the road surface poses risk to both pedestrians and vehicles. Immediate road repair is needed to prevent accidents.","confidence":0.94}

Input: Image of ceiling with damaged panel + "Ceiling panel damaged exposing wires and pipes"
Output: {"hazard_type":"infrastructure_issue","category":"electrical","severity":4,"is_safety_critical":true,"summary":"Damaged ceiling exposing wires and pipes","reasoning":"A ceiling panel has fallen or broken revealing electrical wiring and pipes beneath. This is a high-risk hazard as exposed wires can cause electrocution and falling panels injure occupants.","confidence":0.96}

Input: Image of litter + "Plastic waste left after events at Amphitheatre"
Output: {"hazard_type":"cleanliness_issue","category":"housekeeping","severity":2,"is_safety_critical":false,"summary":"Litter and plastic waste at Amphitheatre","reasoning":"Students left plastic waste and litter after an event. This is a cleanliness issue requiring housekeeping response but poses no immediate safety risk.","confidence":0.91}

Input: Image of barricade + "Barricade blocking service road near hostel"
Output: {"hazard_type":"access_issue","category":"security","severity":2,"is_safety_critical":false,"summary":"Barricade blocking pathway near hostel","reasoning":"A barricade is obstructing the service road causing inconvenience to students. This needs to be addressed by the security or facilities team to restore access.","confidence":0.88}

Input: Image of dried plants + "Plants in flower pots are dried and not maintained"
Output: {"hazard_type":"maintenance_issue","category":"landscaping","severity":1,"is_safety_critical":false,"summary":"Dried unmaintained plants near walkway","reasoning":"Plants in the flower pots are visibly dried and dead due to lack of maintenance. This is a minor aesthetic issue affecting campus greenery with no safety risk.","confidence":0.90}

━━━━━━━━━━━━━━━━
DECISION RULES
━━━━━━━━━━━━━━━━
- Waterlogging ALWAYS maps to category: civil
- Lighting issues ALWAYS map to category: electrical
- Cleanliness/litter ALWAYS maps to category: housekeeping
- Dried plants / garden neglect maps to category: landscaping
- Barricades / blocked access maps to category: security
- Default for structural, road, leakage issues: civil
- If wires are exposed in a ceiling/infrastructure issue, use category: electrical and is_safety_critical: true
- If the image shows a normal campus scene with no visible problem, return not_a_hazard
- Confidence < 0.6 means you are uncertain — still classify, but note uncertainty in reasoning

Return ONLY this JSON — no markdown, no text before or after:
{
  "hazard_type": "<type from list above>",
  "category": "<electrical|civil|security|housekeeping|landscaping|other>",
  "severity": <1-5>,
  "is_safety_critical": <true|false>,
  "summary": "<one-line title, max 10 words>",
  "reasoning": "<2-3 sentences explaining classification and severity>",
  "confidence": <0.0-1.0>
}"""


# ── Keyword fallback (dataset-aligned) ───────────────────────────────────────

KEYWORD_RULES = [
    # waterlogging
    (["water", "flood", "waterlog", "puddle", "rain", "accumulate", "slippery"],
     "waterlogging", "civil", 3, False),
    # lighting
    (["light", "dark", "lamp", "bulb", "street light", "no light", "lighting"],
     "lighting_issue", "electrical", 2, False),
    # exposed wiring (check before infrastructure)
    (["wire", "wiring", "electric shock", "sparking", "live wire", "electri"],
     "exposed_wiring", "electrical", 4, True),
    # fire
    (["fire", "smoke", "burn", "flame", "blaze"],
     "fire_risk", "civil", 5, True),
    # infrastructure
    (["pothole", "crack", "broken", "damage", "ceiling", "structural", "tile", "pavement", "road"],
     "infrastructure_issue", "civil", 3, False),
    # maintenance
    (["paint", "peel", "leak", "stain", "rust", "plant", "dry", "dead plant", "sculpture"],
     "maintenance_issue", "civil", 2, False),
    # cleanliness
    (["litter", "garbage", "waste", "trash", "dustbin", "dirty", "clean", "sweep", "leaves"],
     "cleanliness_issue", "housekeeping", 1, False),
    # access
    (["block", "barricade", "obstruct", "access", "pathway", "gate"],
     "access_issue", "security", 2, False),
    # security
    (["suspicious", "weapon", "fight", "threat", "stalker", "theft"],
     "suspicious_activity", "security", 4, True),
]


def _keyword_classify(text: str, fallback_reason: str = "Gemini API unavailable") -> dict:
    text_lower = text.lower()
    for keywords, hazard_type, category, severity, critical in KEYWORD_RULES:
        if any(kw in text_lower for kw in keywords):
            return _apply_ml_severity(_enrich_with_taxonomy({
                "hazard_type": hazard_type,
                "category": category,
                "severity": severity,
                "is_safety_critical": critical,
                "summary": f"Possible {hazard_type.replace('_', ' ')} detected",
                "reasoning": f"{fallback_reason}. Keyword rules were used to identify the hazard type.",
                "confidence": 0.5,
            }), text)
    return _apply_ml_severity(_enrich_with_taxonomy({
        "hazard_type": "other",
        "category": "other",
        "severity": 2,
        "is_safety_critical": False,
        "summary": "Campus hazard reported",
        "reasoning": f"{fallback_reason}. Could not determine hazard type automatically.",
        "confidence": 0.3,
    }), text)


def _apply_ml_severity(result: dict, text: str) -> dict:
    prediction = predict_severity(text)
    if not prediction:
        return result

    ai_severity = int(result.get("severity") or prediction["severity"])
    ml_severity = prediction["severity"]
    result["ml_severity"] = ml_severity
    result["ml_severity_confidence"] = prediction["confidence"]
    result["ml_model"] = prediction["model"]
    # Keep Gemini/rule reasoning dominant, while using the local model as a
    # calibrated signal for ambiguous text-only reports.
    result["severity"] = max(1, min(5, round(ai_severity * 0.7 + ml_severity * 0.3)))
    reasoning_lower = result.get("reasoning", "").lower()
    if "unavailable" in reasoning_lower or "quota" in reasoning_lower:
        result["confidence"] = prediction["confidence"]
        fallback_reason = result["reasoning"].split(".")[0]
        result["reasoning"] = (
            f"{fallback_reason}. Local ML model {prediction['model']} classified "
            f"this report at severity {ml_severity}/5 with {prediction['confidence']:.0%} confidence. "
            "Keyword rules were used to identify the hazard type."
        )
    else:
        result["reasoning"] = f"{result['reasoning']} Local ML severity estimate: {ml_severity}/5 ({prediction['confidence']:.0%} confidence)."
    return result


def _enrich_with_taxonomy(result: dict) -> dict:
    """Map AI output category to taxonomy department ids for routing."""
    simple = result.get("category", "other")
    hazard = result.get("hazard_type", "other")

    # Hazard-type-specific routing (highest priority)
    _hazard_dept = {
        "fire_risk":          "fire_safety_services",
        "exposed_wiring":     "electrical_services",
        "waterlogging":       "civil_plumbing_services",
        "lighting_issue":     "electrical_services",
        "infrastructure_issue": "civil_plumbing_services",
        "maintenance_issue":  "facility_services",
        "cleanliness_issue":  "housekeeping_services",
        "access_issue":       "security_services",
        "suspicious_activity":"security_services",
        "unsafe_structure":   "civil_plumbing_services",
    }

    # Category fallback
    _cat_dept = {
        "electrical":   "electrical_services",
        "civil":        "civil_plumbing_services",
        "security":     "security_services",
        "housekeeping": "housekeeping_services",
        "landscaping":  "landscaping_campus_maintenance",
        "other":        "facility_services",
    }

    dept = _hazard_dept.get(hazard) or _cat_dept.get(simple, "facility_services")
    result["category_simple"] = simple
    result["category"] = dept
    result["service_id"] = None   # user can refine in the stepper
    return result


def _extract_json(text: str) -> Optional[dict]:
    """Extract JSON from model response, handling markdown code blocks."""
    text = re.sub(r"```(?:json)?", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


async def classify_report(image_path: Optional[str], text: str) -> dict:
    """
    Classify a hazard report using Gemini multimodal.
    System prompt is informed by 26 labeled SRM KTR campus images.
    Falls back to keyword classifier on API failure.
    """
    if settings.ai_provider.lower() == "ollama" and text:
        try:
            raw = generate_text(
                f"Report description: {text}",
                system=SYSTEM_PROMPT,
            )
            data = extract_json(raw)
            if data:
                result = ClassificationResult(**data).dict()
                result["reasoning"] = f"Analyzed locally with Ollama ({settings.ollama_model}). {result['reasoning']}"
                return _apply_ml_severity(_enrich_with_taxonomy(result), text)
        except Exception as exc:
            logger.warning("Ollama classification failed: %s", exc)

    if not settings.gemini_api_key:
        logger.warning("No GEMINI_API_KEY set — using keyword classifier")
        return _keyword_classify(text, "Gemini API not configured")

    try:
        parts = [SYSTEM_PROMPT]

        if image_path and os.path.exists(image_path):
            img = Image.open(image_path)
            parts.append(img)

        if text:
            parts.append(f"\nReport description: {text}")
        elif not image_path:
            return _keyword_classify("", "Gemini API not configured")

        response = generate_with_fallback(parts)
        raw = response.text

        data = _extract_json(raw)
        if data is None:
            logger.warning("Malformed JSON from Gemini, retrying...")
            response = generate_with_fallback(parts + ["\nIMPORTANT: Return ONLY a valid JSON object. No markdown, no explanation."])
            data = _extract_json(response.text)

        if data is None:
            logger.error("Gemini returned non-JSON twice, falling back to keywords")
            return _keyword_classify(text, "Gemini response was invalid")

        result = ClassificationResult(**data)
        return _apply_ml_severity(_enrich_with_taxonomy(result.dict()), text)

    except Exception as e:
        logger.error(f"Gemini API error: {e}. Falling back to keyword classifier.")
        error_text = str(e).lower()
        reason = "Gemini quota exceeded" if "quota" in error_text or "429" in error_text else "Gemini unavailable"
        return _keyword_classify(text, reason)
