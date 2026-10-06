"""
Smart routing — maps taxonomy department id to a named department and
auto-assigns to the least-loaded authority user in that department.
"""
import logging
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Report, User, UserRole, ReportStatus, StatusLog
from app.services.notifier import notify_assigned
from app.core.taxonomy import DEPARTMENT_LABELS, DEPARTMENTS

logger = logging.getLogger(__name__)

# Map taxonomy department id -> user-facing department name (matches User.department)
# Departments that don't have dedicated authority accounts fall back to "Admin"
TAXONOMY_TO_DEPT: dict[str, str] = {
    "architect_services": "Architect Services",
    "facility_services": "Facility Management",
    "hostel_services": "Hostel Management",
    "transport_services": "Transport",
    "security_services": "Security",
    "housekeeping_services": "Housekeeping",
    "electrical_services": "Electrical",
    "civil_plumbing_services": "Civil",
    "fire_safety_services": "Fire & Safety",
    "hvac_ac_services": "HVAC",
    "it_telecom_services": "IT & Telecom",
    "laundry_services": "Hostel Management",
    "mess_food_services": "Hostel Management",
    "transport_parking": "Transport",
    "landscaping_campus": "Civil",
    "waste_management": "Housekeeping",
    "student_admin_services": "Admin",
    "medical_health_services": "Medical",
    "library_services": "Admin",
    "sports_recreation": "Admin",
    "labs_technical": "Admin",
    "procurement_stores": "Admin",
    "environment_sustainability": "Civil",
    "events_campus_facilities": "Admin",
    # Legacy 4-category support
    "electrical": "Electrical",
    "civil": "Civil",
    "security": "Security",
    "other": "Admin",
}

# Accept both the taxonomy IDs used by new registrations and the legacy labels
# used by seeded authority accounts while the existing database is upgraded.
DEPARTMENT_VALUES: dict[str, set[str]] = {
    taxonomy_id: {taxonomy_id, department}
    for taxonomy_id, department in TAXONOMY_TO_DEPT.items()
}
DEPARTMENT_VALUES["civil_plumbing_services"].add("Civil/Maintenance")


def department_values(department: str) -> set[str]:
    for values in DEPARTMENT_VALUES.values():
        if department in values:
            return values
    return {department}


def route_report(report: Report, db: Session) -> None:
    """
    Auto-assign a report to the least-loaded authority in the appropriate department.
    Sets status to 'assigned' and writes a StatusLog entry.
    """
    category = report.category or "other"
    department = TAXONOMY_TO_DEPT.get(category, "Admin")
    report.assigned_department = department

    # Find least-loaded authority in this department
    open_statuses = [ReportStatus.assigned, ReportStatus.in_progress]
    authority = (
        db.query(User)
        .filter(
            User.role == UserRole.authority,
            User.department.in_(department_values(department)),
        )
        .outerjoin(
            Report,
            (Report.assigned_to == User.id) & (Report.status.in_(open_statuses))
        )
        .group_by(User.id)
        .order_by(func.count(Report.id).asc())
        .first()
    )

    old_status = report.status.value if report.status else "reported"

    if authority:
        report.assigned_to = authority.id
        report.status = ReportStatus.assigned
        log = StatusLog(
            report_id=report.id,
            old_status=old_status,
            new_status=ReportStatus.assigned.value,
            changed_by=authority.id,
            note=f"Auto-assigned to {authority.name} ({department})",
        )
        db.add(log)
        db.commit()
        notify_assigned(db, report)
        logger.info(f"Report #{report.id} routed to {authority.name} ({department})")
    else:
        # No authority available — assign to any admin
        admin = db.query(User).filter(User.role == UserRole.admin).first()
        if admin:
            report.assigned_to = admin.id
        report.assigned_department = department
        report.status = ReportStatus.assigned
        log = StatusLog(
            report_id=report.id,
            old_status=old_status,
            new_status=ReportStatus.assigned.value,
            changed_by=admin.id if admin else report.reporter_id,
            note=f"Routed to {department} — no authority available, assigned to admin queue.",
        )
        db.add(log)
        db.commit()
        logger.warning(
            f"No authority for {department}, report #{report.id} assigned to admin"
        )
