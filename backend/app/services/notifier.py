"""
Notification service — in-app, email (SMTP), and mock SMS/WhatsApp.
"""
import logging
import smtplib
from email.mime.text import MIMEText
from typing import Optional
from sqlalchemy.orm import Session

from app.models import Notification, User, Report, UserRole
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _create_in_app(db: Session, user_id: int, report_id: Optional[int], message: str) -> Notification:
    notif = Notification(
        user_id=user_id,
        report_id=report_id,
        message=message,
        channel="in_app",
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


def _send_email(to_email: str, subject: str, body: str):
    if not settings.email_enabled:
        logger.info(f"[EMAIL MOCK] To: {to_email} | Subject: {subject} | Body: {body[:80]}")
        return
    try:
        msg = MIMEText(body, "plain")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_user
        msg["To"] = to_email
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_user, to_email, msg.as_string())
    except Exception as e:
        logger.error(f"Email send failed: {e}")


def _send_sms_mock(phone: str, message: str):
    """Mock SMS adapter — logs to console. Replace with Twilio/etc. in production."""
    logger.info(f"[SMS MOCK] To: {phone} | Message: {message}")


def _send_whatsapp_mock(phone: str, message: str):
    """Mock WhatsApp adapter — logs to console."""
    logger.info(f"[WHATSAPP MOCK] To: {phone} | Message: {message}")


def notify_user(
    db: Session,
    user_id: int,
    message: str,
    report_id: Optional[int] = None,
    subject: str = "S.O.S. Campus Alert",
):
    """Create in-app notification and optionally send email."""
    _create_in_app(db, user_id, report_id, message)

    user = db.query(User).filter(User.id == user_id).first()
    if user:
        _send_email(user.email, subject, message)


def notify_assigned(db: Session, report: Report):
    """Notify reporter that their report was assigned."""
    notify_user(
        db,
        report.reporter_id,
        f"Your report ''{report.title}'' has been assigned to {report.assigned_department}.",
        report.id,
        "Report Assigned — S.O.S.",
    )


def notify_status_change(db: Session, report: Report, old_status: str, new_status: str):
    notify_user(
        db,
        report.reporter_id,
        f"Your report ''{report.title}'' status changed from {old_status} to {new_status}.",
        report.id,
        "Report Status Update — S.O.S.",
    )


def notify_duplicate_merged(db: Session, reporter_id: int, parent_report: Report):
    notify_user(
        db,
        reporter_id,
        f"A similar issue already exists (#{parent_report.id}: {parent_report.title}). "
        "Your report was merged and the original has been hyped on your behalf.",
        parent_report.id,
        "Report Merged — S.O.S.",
    )


def notify_resolved(db: Session, report: Report):
    notify_user(
        db,
        report.reporter_id,
        f"Your report ''{report.title}'' has been resolved. Please confirm the fix.",
        report.id,
        "Issue Resolved — S.O.S.",
    )


def notify_disputed(db: Session, report: Report):
    if report.assigned_to:
        notify_user(
            db,
            report.assigned_to,
            f"Reporter disputed the closure of ''{report.title}''. Issue reopened.",
            report.id,
            "Report Disputed — S.O.S.",
        )


def notify_safety_critical(db: Session, report: Report):
    """Alert all Security and Admin users immediately."""
    users = db.query(User).filter(
        User.role.in_([UserRole.authority, UserRole.admin])
    ).all()
    for user in users:
        if user.department in ("Security", None) or user.role == UserRole.admin:
            notify_user(
                db,
                user.id,
                f"⚠️ SAFETY CRITICAL: ''{report.title}'' at {report.building} requires immediate attention!",
                report.id,
                "🚨 Safety Critical Alert — S.O.S.",
            )
