import os
import shutil
import uuid
from datetime import datetime, date, timedelta
from typing import Optional, List
from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile, File, Form,
    Query, BackgroundTasks
)
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from app.database import get_db
from app.models import Report, User, Hype, StatusLog, UserRole, ReportStatus, Verification, Location
from app.schemas import (
    ReportOut, ReportListItem, PaginatedReports, StatusUpdate,
    AssignUpdate, HypeOut, StatusLogOut, PriorityBreakdown, VerificationOut
)
from app.routers.auth import get_current_user, require_role
from app.services.ai_classifier import classify_report
from app.services.duplicate_detector import find_similar, compute_and_store_embedding
from app.services.priority_engine import compute_priority, update_priority
from app.services.router import route_report
from app.services.notifier import (
    notify_status_change, notify_resolved, notify_disputed,
    notify_safety_critical, notify_duplicate_merged
)
from app.core.config import get_settings

router = APIRouter(prefix="/reports", tags=["reports"])
settings = get_settings()

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


def _build_report_out(report: Report, current_user: User, db: Session) -> ReportOut:
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

    return ReportOut(
        id=report.id,
        title=report.title,
        description=report.description,
        image_path=report.image_path,
        building=report.building,
        zone=report.zone,
        lat=report.lat,
        lng=report.lng,
        hazard_type=report.hazard_type,
        category=report.category,
        severity=report.severity,
        is_safety_critical=report.is_safety_critical,
        ai_summary=report.ai_summary,
        ai_reasoning=report.ai_reasoning,
        ai_confidence=report.ai_confidence,
        status=report.status,
        assigned_department=report.assigned_department,
        priority_score=report.priority_score,
        hype_count=report.hype_count,
        recurrence_count=report.recurrence_count,
        duplicate_of=report.duplicate_of,
        is_anonymous=report.is_anonymous,
        created_at=report.created_at,
        updated_at=report.updated_at,
        resolved_at=report.resolved_at,
        reporter_name=report.reporter.name if show_reporter else "Anonymous",
        reporter_id=report.reporter_id if show_reporter else None,
        current_user_hyped=user_hyped,
        status_history=status_history,
        priority_breakdown=pb,
    )


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
    image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    image_path = None
    if image:
        if image.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(400, "Only JPEG, PNG, WebP, GIF images allowed")
        image_path = _save_upload(image)

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
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # AI classification
    ai_result = await classify_report(image_path, description or title)
    report.hazard_type = ai_result.get("hazard_type")
    report.category = ai_result.get("category")
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
        q = q.filter(Report.assigned_department == department)

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
            hazard_type=r.hazard_type,
            category=r.category,
            severity=r.severity,
            is_safety_critical=r.is_safety_critical,
            status=r.status,
            priority_score=r.priority_score,
            hype_count=r.hype_count,
            recurrence_count=r.recurrence_count,
            is_anonymous=r.is_anonymous,
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
            hazard_type=r.hazard_type, category=r.category, severity=r.severity,
            is_safety_critical=r.is_safety_critical, status=r.status,
            priority_score=r.priority_score, hype_count=r.hype_count,
            recurrence_count=r.recurrence_count, is_anonymous=r.is_anonymous,
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
    return _build_report_out(report, current_user, db)


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

    # AI verification
    ai_match = {"same_location": None, "issue_resolved": None, "confidence": None}
    if settings.gemini_api_key:
        try:
            import google.generativeai as genai
            from PIL import Image as PILImage
            import json as _json

            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            parts = ["Compare these two campus images and return ONLY JSON: "
                     '{"same_location": true/false, "issue_resolved": true/false, "confidence": 0.0-1.0}']
            if report.image_path and os.path.exists(report.image_path):
                parts.append(PILImage.open(report.image_path))
            parts.append(PILImage.open(after_path))
            response = model.generate_content(parts)
            raw = response.text
            import re
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                ai_match = _json.loads(m.group())
        except Exception as e:
            pass

    flagged = (
        ai_match.get("confidence") is not None
        and ai_match["confidence"] < 0.6
    )

    verif = Verification(
        report_id=report_id,
        after_image_path=after_path,
        verified_by_authority=current_user.id,
        ai_match_score=ai_match.get("confidence"),
        ai_same_location=ai_match.get("same_location"),
        ai_issue_resolved=ai_match.get("issue_resolved"),
        flagged_for_review=flagged,
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
