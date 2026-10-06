"""
Feature 4: Weekly AI Digest
GET /analytics/digest  (admin only) — generates a Gemini-written weekly campus health summary.
POST /analytics/digest/generate — force-generate now (for demo).
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Report, ReportStatus, User, UserRole
from app.core.config import get_settings
from app.core.gemini import generate_with_fallback
from app.services.ollama import extract_json, generate_text
from app.services.router import department_values

logger = logging.getLogger(__name__)
settings = get_settings()

DIGEST_PROMPT = """You are the AI Campus Health Monitor for SRM University KTR.
Every week you analyse the campus hazard report data and write a concise, professional
weekly digest for the Admin team.

Here is the data for the past 7 days:

{data}

Write a well-structured digest with these sections. Be specific — use the actual numbers,
building names, and department names from the data. Keep a professional but approachable tone.
Do NOT invent data; only use what is given.

Return ONLY valid JSON — no markdown, no extra text:
{{
  "week_summary": "<2-3 sentence overview of the week's campus health>",
  "top_issue": {{
    "title": "<the most critical or frequent issue type>",
    "detail": "<1-2 sentences with specifics>"
  }},
  "department_spotlight": {{
    "fastest": "<department that resolved issues fastest, with avg hours>",
    "needs_attention": "<department with most open/overdue issues>"
  }},
  "hotspot_building": {{
    "name": "<building with most reports>",
    "count": <number>,
    "main_issue": "<most common issue type there>"
  }},
  "pattern_to_watch": "<one emerging pattern or recurring issue worth monitoring>",
  "positive_highlight": "<something that went well this week>",
  "recommendations": [
    "<actionable recommendation 1>",
    "<actionable recommendation 2>",
    "<actionable recommendation 3>"
  ],
  "stats": {{
    "total_reports": <number>,
    "resolved": <number>,
    "open": <number>,
    "safety_critical": <number>,
    "avg_resolution_hours": <number or null>
  }}
}}"""


def _collect_week_data(db: Session, department: Optional[str] = None) -> dict:
    """Collect report statistics for the past 7 days and optional department scope."""
    week_ago = datetime.utcnow() - timedelta(days=7)

    query = db.query(Report).filter(Report.created_at >= week_ago)
    if department:
        query = query.filter(Report.assigned_department.in_(department_values(department)))
    reports = query.all()
    total = len(reports)
    resolved = sum(1 for r in reports if r.status == ReportStatus.resolved)
    open_count = total - resolved
    critical = sum(1 for r in reports if r.is_safety_critical)

    # Avg resolution time (hours)
    resolution_times = []
    for r in reports:
        if r.status == ReportStatus.resolved and r.resolved_at and r.created_at:
            hrs = (r.resolved_at - r.created_at).total_seconds() / 3600
            resolution_times.append(hrs)
    avg_resolution = round(sum(resolution_times) / len(resolution_times), 1) if resolution_times else None

    # Building breakdown
    building_counts = {}
    for r in reports:
        building_counts[r.building] = building_counts.get(r.building, 0) + 1
    top_building = max(building_counts, key=building_counts.get) if building_counts else "N/A"
    top_building_count = building_counts.get(top_building, 0)

    # Hazard type breakdown
    hazard_counts = {}
    for r in reports:
        ht = r.hazard_type or "other"
        hazard_counts[ht] = hazard_counts.get(ht, 0) + 1
    top_hazard = max(hazard_counts, key=hazard_counts.get) if hazard_counts else "other"
    top_hazard_count = hazard_counts.get(top_hazard, 0)

    # Department breakdown
    dept_counts = {}
    dept_resolved = {}
    for r in reports:
        dept = r.assigned_department or "Unassigned"
        dept_counts[dept] = dept_counts.get(dept, 0) + 1
        if r.status == ReportStatus.resolved:
            dept_resolved[dept] = dept_resolved.get(dept, 0) + 1

    # Department with most open issues
    dept_open = {}
    for r in reports:
        if r.status != ReportStatus.resolved:
            dept = r.assigned_department or "Unassigned"
            dept_open[dept] = dept_open.get(dept, 0) + 1
    needs_attention_dept = max(dept_open, key=dept_open.get) if dept_open else "N/A"

    # Building with most reports for top hazard
    top_building_hazard = {}
    for r in reports:
        if r.building == top_building:
            ht = r.hazard_type or "other"
            top_building_hazard[ht] = top_building_hazard.get(ht, 0) + 1
    top_building_main_issue = max(top_building_hazard, key=top_building_hazard.get) if top_building_hazard else "other"

    return {
        "period": f"{week_ago.strftime('%d %b')} – {datetime.utcnow().strftime('%d %b %Y')}",
        "department_scope": department or "All departments",
        "total_reports": total,
        "resolved": resolved,
        "open": open_count,
        "safety_critical": critical,
        "avg_resolution_hours": avg_resolution,
        "top_building": top_building,
        "top_building_count": top_building_count,
        "top_building_main_issue": top_building_main_issue,
        "top_hazard_type": top_hazard,
        "top_hazard_count": top_hazard_count,
        "hazard_breakdown": hazard_counts,
        "department_open_counts": dept_open,
        "department_resolved_counts": dept_resolved,
        "needs_attention_dept": needs_attention_dept,
        "all_buildings": dict(sorted(building_counts.items(), key=lambda x: -x[1])[:5]),
    }


def _build_fallback_digest(data: dict, *, error: Optional[str] = None) -> dict:
    payload = {
        "generated_at": datetime.utcnow().isoformat(),
        "period": data["period"],
        "department_scope": data["department_scope"],
        "ai_available": False,
        "stats": {
            "total_reports": data["total_reports"],
            "resolved": data["resolved"],
            "open": data["open"],
            "safety_critical": data["safety_critical"],
            "avg_resolution_hours": data["avg_resolution_hours"],
        },
        "week_summary": f"{data['total_reports']} reports this week. {data['resolved']} resolved, {data['open']} still open.",
        "top_issue": {"title": data["top_hazard_type"], "detail": f"{data['top_hazard_count']} occurrences."},
        "hotspot_building": {"name": data["top_building"], "count": data["top_building_count"], "main_issue": data["top_building_main_issue"]},
        "pattern_to_watch": "Review open safety-critical reports.",
        "positive_highlight": f"{data['resolved']} issues resolved this week.",
        "recommendations": ["Prioritise safety-critical open reports.", "Inspect hotspot building.", "Schedule drainage check before next rain."],
        "department_spotlight": {"fastest": "N/A", "needs_attention": data["needs_attention_dept"]},
    }
    if error:
        payload["generation_error"] = error
    return payload


async def generate_weekly_digest(db: Session, department: Optional[str] = None) -> dict:
    """Generate the AI weekly digest using Gemini."""
    data = _collect_week_data(db, department)

    if settings.ai_provider.lower() == "ollama":
        try:
            prompt = DIGEST_PROMPT.format(data=json.dumps(data, indent=2))
            digest = extract_json(generate_text(prompt))
            if digest:
                digest["generated_at"] = datetime.utcnow().isoformat()
                digest["period"] = data["period"]
                digest["department_scope"] = data["department_scope"]
                digest["ai_available"] = True
                digest["ai_provider"] = f"ollama/{settings.ollama_model}"
                return digest
        except Exception as exc:
            logger.warning("Ollama digest generation failed: %s", exc)

    if not settings.gemini_api_key:
        return _build_fallback_digest(data)

    try:
        prompt = DIGEST_PROMPT.format(data=json.dumps(data, indent=2))
        response = generate_with_fallback(prompt)

        import re
        text = re.sub(r"```(?:json)?", "", response.text).strip()
        digest = json.loads(text)
        digest["generated_at"] = datetime.utcnow().isoformat()
        digest["period"] = data["period"]
        digest["department_scope"] = data["department_scope"]
        digest["ai_available"] = True
        digest.setdefault("department_spotlight", {"fastest": "N/A", "needs_attention": data["needs_attention_dept"]})
        return digest

    except Exception as e:
        logger.error(f"Digest generation error: {e}")
        return _build_fallback_digest(data, error=str(e))
