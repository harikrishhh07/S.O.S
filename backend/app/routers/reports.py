import os
import shutil
import uuid
import logging
from datetime import datetime, date, timedelta
from typing import Optional, List
from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile, File, Form,
    Query, BackgroundTasks
)
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from app.database import get_db
from app.models import Report, User, Hype, StatusLog, Notification, UserRole, ReportStatus, Verification, Location
from app.schemas import (
    ReportOut, ReportListItem, PaginatedReports, StatusUpdate,
    AssignUpdate, HypeOut, StatusLogOut, PriorityBreakdown, VerificationOut
)
from app.routers.auth import get_current_user, require_role
from app.services.ai_classifier import classify_report
from app.services.ml_severity import predict_severity
from app.services.duplicate_detector import find_similar, compute_and_store_embedding
from app.services.priority_engine import compute_priority, update_priority
from app.services.router import route_report
from app.services.router import department_values
from app.services.location_inference import infer_location_from_image
from app.services.ollama import extract_json, generate_text
from app.services.notifier import (
    notify_status_change, notify_resolved, notify_disputed,
    notify_safety_critical, notify_duplicate_merged
)
from app.core.config import get_settings
from app.core.gemini import generate_with_fallback

router = APIRouter(prefix="/reports", tags=["reports"])
settings = get_settings()
logger = logging.getLogger(__name__)

HYPE_DAILY_LIMIT = 20
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def _save_upload(file: UploadFile) -> str:
    """Save an uploaded file to the uploads directory and return its path."""
    os.makedirs(settings.upload_dir, exist_ok=True)
    ext = os.path.splitext(file.filename)[-1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(settings.upload_dir, filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return path


def _build_report_out(report: Report, current_user: User, db: Session, use_live_ai: bool = False) -> ReportOut:
    """Hydrate a ReportOut with computed fields."""
    # Hide reporter identity for anonymous reports (unless admin)
    show_reporter = (
        current_user.role == UserRole.admin
        or report.reporter_id == current_user.id
        or not report.is_anonymous
    )

    status_logs = db.query(StatusLog).filter(
        StatusLog.report_id == report.id
    ).order_by(StatusLog.created_at).all()

    status_history = []
    for log in status_logs:
        changer = db.query(User).filter(User.id == log.changed_by).first()
        status_history.append(StatusLogOut(
            id=log.id,
            old_status=log.old_status,
            new_status=log.new_status,
            note=log.note,
            created_at=log.created_at,
            changer_name=changer.name if changer else None,
        ))

    user_hyped = db.query(Hype).filter(
        Hype.report_id == report.id,
        Hype.user_id == current_user.id
    ).first() is not None

    # Priority breakdown
    loc = db.query(Location).filter(Location.building == report.building).first()
    breakdown = compute_priority(report, location_criticality=loc.criticality if loc else 3)
    pb = PriorityBreakdown(**breakdown)

    ml_prediction = predict_severity(
        " ".join(part for part in (report.title, report.description, report.building, report.zone) if part)
    )
    ai_reasoning = report.ai_reasoning
    ai_confidence = report.ai_confidence
    is_local_fallback = any(
        marker in (ai_reasoning or "")
        for marker in ("AI unavailable", "keyword matching", "quota exceeded")
    )
    if ml_prediction and is_local_fallback:
        ai_reasoning = (
            f"Gemini fallback used. Local ML model {ml_prediction['model']} classified "
            f"this report at severity {ml_prediction['severity']}/5 with "
            f"{ml_prediction['confidence']:.0%} confidence. Keyword rules were used "
            "to identify the hazard type."
        )
    elif ml_prediction and "Local ML severity estimate" not in (ai_reasoning or ""):
        ml_note = (
            f"Local ML severity estimate: {ml_prediction['severity']}/5 "
            f"({ml_prediction['confidence']:.0%} confidence)."
        )
        ai_reasoning = f"{ai_reasoning} {ml_note}" if ai_reasoning else ml_note
    if ml_prediction and is_local_fallback:
        ai_confidence = ml_prediction["confidence"]

    if use_live_ai and settings.ai_provider.lower() == "ollama" and is_local_fallback:
        try:
            ollama_result = extract_json(generate_text(
                "Analyze this campus hazard report and return JSON with exactly these keys: "
                "reasoning (a concise explanation), confidence (number from 0 to 1), "
                "severity (integer from 1 to 5).\n"
                f"Title: {report.title}\nDescription: {report.description or ''}\n"
                f"Building: {report.building}\nCurrent severity: {report.severity}",
                system="You are the local Ollama safety analyst for a campus hazard reporting system.",
            ))
            if ollama_result:
                ai_reasoning = f"Ollama ({settings.ollama_model}): {ollama_result.get('reasoning', ai_reasoning)}"
                ai_confidence = float(ollama_result.get("confidence", ai_confidence or 0))
        except Exception as exc:
            logger.warning("Live Ollama report analysis failed: %s", exc)

    verif = report.verification if hasattr(report, 'verification') else None
    verif_out = None
    if verif:
        verif_out = {
            "id": verif.id,
            "after_image_path": verif.after_image_path,
            "reporter_confirmed": verif.reporter_confirmed,
            "ai_match_score": verif.ai_match_score,
            "ai_same_location": verif.ai_same_location,
            "ai_issue_resolved": verif.ai_issue_resolved,
            "flagged_for_review": verif.flagged_for_review,
            "ai_fix_quality": getattr(verif, 'ai_fix_quality', None),
            "ai_fix_quality_score": getattr(verif, 'ai_fix_quality_score', None),
            "ai_durability_risk": getattr(verif, 'ai_durability_risk', None),
            "ai_follow_up_days": getattr(verif, 'ai_follow_up_days', None),
            "ai_quality_reasoning": getattr(verif, 'ai_quality_reasoning', None),
            "created_at": verif.created_at,
        }

    return ReportOut(
        id=report.id,
        title=report.title,
        description=report.description,
        image_path=report.image_path,
        building=report.building,
        zone=report.zone,
        lat=report.lat,
        lng=report.lng,
        hazard_type=report.hazard_type.value if report.hazard_type else None,
        category=report.category,
        service_id=getattr(report, 'service_id', None),
        severity=report.severity,
        is_safety_critical=report.is_safety_critical or False,
        ai_summary=report.ai_summary,
        ai_reasoning=ai_reasoning,
        ai_confidence=ai_confidence,
        ml_severity=ml_prediction["severity"] if ml_prediction else None,
        ml_severity_confidence=ml_prediction["confidence"] if ml_prediction else None,
        ml_model=ml_prediction["model"] if ml_prediction else None,
        status=report.status,
        assigned_department=report.assigned_department,
        priority_score=report.priority_score or 0.0,
        hype_count=report.hype_count or 0,
        recurrence_count=report.recurrence_count or 0,
        duplicate_of=report.duplicate_of,
        is_anonymous=report.is_anonymous or False,
        created_at=report.created_at,
        updated_at=report.updated_at,
        resolved_at=report.resolved_at,
        reporter_name=report.reporter.name if show_reporter else "Anonymous",
        reporter_id=report.reporter_id if show_reporter else None,
        current_user_hyped=user_hyped,
        status_history=status_history,
        priority_breakdown=pb,
        verification=verif_out,
    )


@router.post("/infer-location")
async def infer_location_endpoint(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Feature 2: Smart Location Inference.
    Upload a photo -> Gemini identifies the SRM KTR building and zone.
    Frontend uses the result to auto-select the building dropdown.
    """
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(400, "Only JPEG, PNG, WebP images allowed")
    image_path = _save_upload(image)
    result = await infer_location_from_image(image_path)
    return {
        "building": result.building,
        "zone": result.zone,
        "landmark_clues": result.landmark_clues,
        "confidence": result.confidence,
        "alternative": result.alternative,
    }


@router.post("", status_code=201)
async def create_report(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    building: str = Form(...),
    zone: Optional[str] = Form(None),
    lat: Optional[float] = Form(None),
    lng: Optional[float] = Form(None),
    is_anonymous: bool = Form(False),
    category: Optional[str] = Form(None),       # taxonomy department id (user override)
    service_id: Optional[str] = Form(None),      # taxonomy sub-service id (user override)
    image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    image_path = None
    if image:
        if image.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(400, "Only JPEG, PNG, WebP, GIF images allowed")
        image_path = _save_upload(image)

    # Feature 2: If building is a placeholder, try to infer from image
    inferred_location = None
    if image_path and (not building or building in ("unknown", "auto", "")):
        inferred_location = await infer_location_from_image(image_path)
        if inferred_location.building:
            building = inferred_location.building
            if not zone and inferred_location.zone:
                zone = inferred_location.zone

    report = Report(
        reporter_id=current_user.id,
        title=title,
        description=description,
        image_path=image_path,
        building=building,
        zone=zone,
        lat=lat,
        lng=lng,
        is_anonymous=is_anonymous,
        service_id=service_id,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # AI classification
    ai_result = await classify_report(image_path, description or title)

    # Coerce hazard_type string -> HazardType enum (safe fallback to 'other')
    from app.models import HazardType as HazardTypeEnum
    raw_ht = ai_result.get("hazard_type") or "other"
    try:
        report.hazard_type = HazardTypeEnum(raw_ht)
    except ValueError:
        report.hazard_type = HazardTypeEnum.other

    # User-selected category overrides AI; fall back to AI result
    report.category = category or ai_result.get("category")
    if service_id and not report.service_id:
        report.service_id = service_id
    report.severity = ai_result.get("severity")
    report.is_safety_critical = ai_result.get("is_safety_critical", False)
    report.ai_summary = ai_result.get("summary")
    report.ai_reasoning = ai_result.get("reasoning")
    report.ai_confidence = ai_result.get("confidence")
    if report.ai_summary and not title:
        report.title = report.ai_summary
    db.commit()

    # Generate embedding
    await compute_and_store_embedding(report, db)

    # Duplicate detection
    dup_result = await find_similar(report, db)
    if dup_result["status"] == "DUPLICATE":
        parent = db.query(Report).filter(Report.id == dup_result["duplicate_of"]).first()
        if parent:
            report.duplicate_of = parent.id
            parent.hype_count += 1
            db.commit()
            notify_duplicate_merged(db, current_user.id, parent)
            update_priority(parent, db)
    elif dup_result["status"] in ("RECURRING",):
        report.recurrence_count = dup_result["recurrence_count"]
        db.commit()

    # Priority score
    update_priority(report, db)

    # Auto-route
    route_report(report, db)

    # Safety critical alert
    if report.is_safety_critical:
        notify_safety_critical(db, report)

    db.refresh(report)
    return {
        "report": _build_report_out(report, current_user, db),
        "ai_result": ai_result,
        "duplicate_check": dup_result,
    }


@router.get("", response_model=PaginatedReports)
def list_reports(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    building: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    sort: str = Query("priority", enum=["priority", "newest", "hype"]),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Report).filter(Report.duplicate_of == None)

    if status:
        q = q.filter(Report.status == status)
    if category:
        q = q.filter(Report.category == category)
    if building:
        q = q.filter(Report.building == building)
    if department:
        q = q.filter(Report.assigned_department.in_(department_values(department)))

    if sort == "priority":
        q = q.order_by(desc(Report.priority_score))
    elif sort == "newest":
        q = q.order_by(desc(Report.created_at))
    elif sort == "hype":
        q = q.order_by(desc(Report.hype_count))

    total = q.count()
    reports = q.offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for r in reports:
        show_reporter = (
            current_user.role == UserRole.admin
            or r.reporter_id == current_user.id
            or not r.is_anonymous
        )
        hyped = db.query(Hype).filter(
            Hype.report_id == r.id, Hype.user_id == current_user.id
        ).first() is not None
        items.append(ReportListItem(
            id=r.id,
            title=r.title,
            building=r.building,
            zone=r.zone,
            hazard_type=r.hazard_type.value if r.hazard_type else None,
            category=r.category,
            service_id=getattr(r, 'service_id', None),
            severity=r.severity,
            is_safety_critical=r.is_safety_critical or False,
            status=r.status,
            priority_score=r.priority_score or 0.0,
            hype_count=r.hype_count or 0,
            recurrence_count=r.recurrence_count or 0,
            is_anonymous=r.is_anonymous or False,
            created_at=r.created_at,
            reporter_name=r.reporter.name if show_reporter else "Anonymous",
            current_user_hyped=hyped,
            image_path=r.image_path,
        ))

    return PaginatedReports(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get("/mine", response_model=List[ReportListItem])
def my_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reports = db.query(Report).filter(
        Report.reporter_id == current_user.id
    ).order_by(desc(Report.created_at)).all()
    return [
        ReportListItem(
            id=r.id, title=r.title, building=r.building, zone=r.zone,
            hazard_type=r.hazard_type.value if r.hazard_type else None,
            category=r.category,
            service_id=getattr(r, 'service_id', None),
            severity=r.severity,
            is_safety_critical=r.is_safety_critical or False,
            status=r.status,
            priority_score=r.priority_score or 0.0,
            hype_count=r.hype_count or 0,
            recurrence_count=r.recurrence_count or 0,
            is_anonymous=r.is_anonymous or False,
            created_at=r.created_at, reporter_name=current_user.name,
            current_user_hyped=False, image_path=r.image_path,
        )
        for r in reports
    ]


@router.get("/{report_id}", response_model=ReportOut)
def get_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(404, "Report not found")
    return _build_report_out(report, current_user, db, use_live_ai=True)


@router.delete("/{report_id}")
def delete_report(
    report_id: int,
    current_user: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    """Permanently remove a report and its dependent records (admin only)."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(404, "Report not found")

    for child_query in (
        db.query(Hype).filter(Hype.report_id == report_id),
        db.query(StatusLog).filter(StatusLog.report_id == report_id),
        db.query(Verification).filter(Verification.report_id == report_id),
    ):
        child_query.delete(synchronize_session=False)

    db.query(Notification).filter(Notification.report_id == report_id).delete(synchronize_session=False)
    image_path = report.image_path
    db.delete(report)
    db.commit()

    if image_path and os.path.exists(image_path):
        os.remove(image_path)

    return {"message": f"Report #{report_id} deleted"}


@router.patch("/{report_id}/status")
def update_status(
    report_id: int,
    data: StatusUpdate,
    current_user: User = Depends(require_role(UserRole.authority, UserRole.admin)),
    db: Session = Depends(get_db),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(404, "Report not found")

    old_status = report.status.value
    report.status = data.status
    if data.status == ReportStatus.resolved:
        report.resolved_at = datetime.utcnow()

    log = StatusLog(
        report_id=report_id,
        old_status=old_status,
        new_status=data.status.value,
        changed_by=current_user.id,
        note=data.note,
    )
    db.add(log)
    db.commit()

    notify_status_change(db, report, old_status, data.status.value)
    update_priority(report, db)

    return {"status": report.status, "message": "Status updated"}


@router.patch("/{report_id}/assign")
def reassign_report(
    report_id: int,
    data: AssignUpdate,
    current_user: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(404, "Report not found")
    new_authority = db.query(User).filter(User.id == data.assigned_to).first()
    if not new_authority:
        raise HTTPException(404, "User not found")

    old_assigned = report.assigned_to
    report.assigned_to = data.assigned_to
    log = StatusLog(
        report_id=report_id,
        old_status=report.status.value,
        new_status=report.status.value,
        changed_by=current_user.id,
        note=data.note or f"Reassigned from user #{old_assigned} to {new_authority.name}",
    )
    db.add(log)
    db.commit()
    return {"message": f"Reassigned to {new_authority.name}"}


@router.post("/{report_id}/hype", response_model=HypeOut)
def add_hype(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(404, "Report not found")
    if report.reporter_id == current_user.id:
        raise HTTPException(400, "You cannot hype your own report")

    # Check daily limit
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_hypes = db.query(Hype).filter(
        Hype.user_id == current_user.id,
        Hype.created_at >= today_start,
    ).count()
    if today_hypes >= HYPE_DAILY_LIMIT:
        raise HTTPException(429, f"Daily hype limit of {HYPE_DAILY_LIMIT} reached")

    existing = db.query(Hype).filter(
        Hype.report_id == report_id, Hype.user_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(400, "Already hyped this report")

    hype = Hype(report_id=report_id, user_id=current_user.id)
    db.add(hype)
    report.hype_count += 1
    db.commit()
    update_priority(report, db)

    return HypeOut(report_id=report_id, hype_count=report.hype_count, current_user_hyped=True)


@router.delete("/{report_id}/hype", response_model=HypeOut)
def remove_hype(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(404, "Report not found")

    hype = db.query(Hype).filter(
        Hype.report_id == report_id, Hype.user_id == current_user.id
    ).first()
    if not hype:
        raise HTTPException(400, "You have not hyped this report")

    db.delete(hype)
    report.hype_count = max(0, report.hype_count - 1)
    db.commit()
    update_priority(report, db)

    return HypeOut(report_id=report_id, hype_count=report.hype_count, current_user_hyped=False)


@router.post("/{report_id}/resolve")
async def resolve_report(
    report_id: int,
    note: str = Form(...),
    after_image: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.authority, UserRole.admin)),
    db: Session = Depends(get_db),
):
    """Authority submits after-photo. Status -> pending_confirmation."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(404, "Report not found")

    after_path = _save_upload(after_image)

    # Feature 8: Enhanced AI Before/After Quality Rating
    ai_match = {
        "same_location": None,
        "issue_resolved": None,
        "confidence": None,
        "fix_quality": None,
        "fix_quality_score": None,
        "durability_risk": None,
        "follow_up_days": None,
        "quality_reasoning": None,
    }
    if settings.gemini_api_key:
        try:
            from PIL import Image as PILImage
            import json as _json, re as _re

            enhanced_prompt = """You are a campus maintenance quality inspector for SRM University KTR.
Compare the BEFORE image (the reported hazard) and the AFTER image (the claimed fix).

Assess:
1. Is it the same location/area? (same_location)
2. Is the hazard visibly resolved? (issue_resolved)
3. How good is the quality of the fix? (fix_quality: excellent/good/temporary/inadequate)
4. Fix quality score 0-100 (fix_quality_score)
5. Will it likely recur? (durability_risk: low/medium/high)
6. If temporary/inadequate — how many days before it needs re-inspection? (follow_up_days: number or null)
7. Short explanation of your assessment (quality_reasoning)
8. Overall confidence in your assessment (confidence: 0.0-1.0)

Fix quality guide:
- excellent (90-100): Permanent structural fix, professionally done, no visible issues
- good (70-89): Proper fix, may need monitoring but unlikely to recur soon
- temporary (40-69): Band-aid fix, likely to recur within weeks (e.g. pothole patch over crack, tape on wire)
- inadequate (0-39): Fix is insufficient, hazard still partially present

Return ONLY valid JSON:
{
  "same_location": true/false,
  "issue_resolved": true/false,
  "fix_quality": "excellent|good|temporary|inadequate",
  "fix_quality_score": 0-100,
  "durability_risk": "low|medium|high",
  "follow_up_days": <number or null>,
  "quality_reasoning": "<2-3 sentences>",
  "confidence": 0.0-1.0
}"""

            parts = [enhanced_prompt]
            if report.image_path and os.path.exists(report.image_path):
                parts.append(PILImage.open(report.image_path))
            parts.append(PILImage.open(after_path))
            parts.append("\nFirst image = BEFORE (the hazard). Second image = AFTER (the fix).")

            response = generate_with_fallback(parts)
            raw = response.text
            raw = _re.sub(r"```(?:json)?", "", raw).strip()
            m = _re.search(r"\{.*\}", raw, _re.DOTALL)
            if m:
                ai_match = _json.loads(m.group())
        except Exception as e:
            logger.error(f"AI quality rating error: {e}")

    # Flag if: low confidence, inadequate fix, or temporary fix on critical issue
    fix_quality = ai_match.get("fix_quality", "good")
    flagged = (
        (ai_match.get("confidence") is not None and ai_match["confidence"] < 0.6)
        or fix_quality == "inadequate"
        or (fix_quality == "temporary" and report.severity >= 4)
        or ai_match.get("durability_risk") == "high"
    )

    verif = Verification(
        report_id=report_id,
        after_image_path=after_path,
        verified_by_authority=current_user.id,
        ai_match_score=ai_match.get("confidence"),
        ai_same_location=ai_match.get("same_location"),
        ai_issue_resolved=ai_match.get("issue_resolved"),
        flagged_for_review=flagged,
        ai_fix_quality=ai_match.get("fix_quality"),
        ai_fix_quality_score=ai_match.get("fix_quality_score"),
        ai_durability_risk=ai_match.get("durability_risk"),
        ai_follow_up_days=ai_match.get("follow_up_days"),
        ai_quality_reasoning=ai_match.get("quality_reasoning"),
    )
    db.add(verif)

    old_status = report.status.value
    report.status = ReportStatus.pending_confirmation
    log = StatusLog(
        report_id=report_id,
        old_status=old_status,
        new_status=ReportStatus.pending_confirmation.value,
        changed_by=current_user.id,
        note=note,
    )
    db.add(log)
    db.commit()
    notify_resolved(db, report)

    return {
        "message": "Resolution submitted. Awaiting reporter confirmation.",
        "ai_match": ai_match,
        "flagged_for_review": flagged,
    }


@router.post("/{report_id}/confirm")
def confirm_resolution(
    report_id: int,
    confirmed: bool = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reporter confirms or disputes the resolution."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(404, "Report not found")
    if report.reporter_id != current_user.id:
        raise HTTPException(403, "Only the reporter can confirm resolution")
    if report.status != ReportStatus.pending_confirmation:
        raise HTTPException(400, "Report is not pending confirmation")

    verif = db.query(Verification).filter(Verification.report_id == report_id).first()
    if verif:
        verif.reporter_confirmed = confirmed

    old_status = report.status.value
    if confirmed:
        report.status = ReportStatus.resolved
        report.resolved_at = datetime.utcnow()
        new_status = "resolved"
    else:
        report.status = ReportStatus.reopened
        new_status = "reopened"
        notify_disputed(db, report)

    log = StatusLog(
        report_id=report_id,
        old_status=old_status,
        new_status=new_status,
        changed_by=current_user.id,
        note="Confirmed by reporter" if confirmed else "Disputed by reporter",
    )
    db.add(log)
    db.commit()
    update_priority(report, db)

    return {"status": report.status, "confirmed": confirmed}


@router.post("/admin/auto-resolve-stale")
def auto_resolve_stale(
    current_user: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    """Auto-resolve pending_confirmation reports older than 72h."""
    cutoff = datetime.utcnow() - timedelta(hours=72)
    stale = db.query(Report).filter(
        Report.status == ReportStatus.pending_confirmation,
        Report.updated_at <= cutoff,
    ).all()
    count = 0
    for report in stale:
        report.status = ReportStatus.resolved
        report.resolved_at = datetime.utcnow()
        verif = db.query(Verification).filter(Verification.report_id == report.id).first()
        if verif:
            verif.reporter_confirmed = True  # auto-confirmed
        log = StatusLog(
            report_id=report.id,
            old_status="pending_confirmation",
            new_status="resolved",
            changed_by=current_user.id,
            note="Auto-resolved after 72h of no reporter response",
        )
        db.add(log)
        count += 1
    db.commit()
    return {"auto_resolved": count}
