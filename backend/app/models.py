from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, UniqueConstraint, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    student = "student"
    authority = "authority"
    admin = "admin"


class ReportStatus(str, enum.Enum):
    reported = "reported"
    assigned = "assigned"
    in_progress = "in_progress"
    pending_confirmation = "pending_confirmation"
    resolved = "resolved"
    reopened = "reopened"


class HazardType(str, enum.Enum):
    # Original types
    exposed_wiring = "exposed_wiring"
    water_leakage = "water_leakage"
    broken_infrastructure = "broken_infrastructure"
    fire_risk = "fire_risk"
    unsafe_structure = "unsafe_structure"
    pothole = "pothole"
    broken_light = "broken_light"
    suspicious_activity = "suspicious_activity"
    sanitation = "sanitation"
    other = "other"
    # Dataset-trained types (SRM KTR campus dataset)
    waterlogging = "waterlogging"
    lighting_issue = "lighting_issue"
    infrastructure_issue = "infrastructure_issue"
    maintenance_issue = "maintenance_issue"
    cleanliness_issue = "cleanliness_issue"
    access_issue = "access_issue"


# Category is now a free String backed by taxonomy.py department ids.
# Kept as a lightweight alias so old code that imports Category still works.
class Category(str, enum.Enum):
    electrical = "electrical"
    civil = "civil"
    security = "security"
    other = "other"
    # Extended — maps to taxonomy department ids
    architect_services = "architect_services"
    facility_services = "facility_services"
    hostel_services = "hostel_services"
    transport_services = "transport_services"
    security_services = "security_services"
    housekeeping_services = "housekeeping_services"
    electrical_services = "electrical_services"
    civil_plumbing_services = "civil_plumbing_services"
    fire_safety_services = "fire_safety_services"
    hvac_ac_services = "hvac_ac_services"
    it_telecom_services = "it_telecom_services"
    laundry_services = "laundry_services"
    mess_food_services = "mess_food_services"
    transport_parking = "transport_parking"
    landscaping_campus = "landscaping_campus"
    waste_management = "waste_management"
    student_admin_services = "student_admin_services"
    medical_health_services = "medical_health_services"
    library_services = "library_services"
    sports_recreation = "sports_recreation"
    labs_technical = "labs_technical"
    procurement_stores = "procurement_stores"
    environment_sustainability = "environment_sustainability"
    events_campus_facilities = "events_campus_facilities"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(200), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.student)
    department = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    reports = relationship("Report", back_populates="reporter", foreign_keys="Report.reporter_id")
    hypes = relationship("Hype", back_populates="user")
    notifications = relationship("Notification", back_populates="user")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    image_path = Column(String(500), nullable=True)
    building = Column(String(100), nullable=False)
    zone = Column(String(100), nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)

    # AI fields
    hazard_type = Column(SAEnum(HazardType), nullable=True)
    category = Column(String(100), nullable=True)       # taxonomy department id
    service_id = Column(String(100), nullable=True)     # taxonomy sub-service id
    severity = Column(Integer, nullable=True)  # 1-5
    is_safety_critical = Column(Boolean, default=False)
    ai_summary = Column(String(300), nullable=True)
    ai_reasoning = Column(Text, nullable=True)
    ai_confidence = Column(Float, nullable=True)

    # Status & routing
    status = Column(SAEnum(ReportStatus), default=ReportStatus.reported)
    assigned_department = Column(String(100), nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Priority
    priority_score = Column(Float, default=0.0)

    # Hype & recurrence
    hype_count = Column(Integer, default=0)
    recurrence_count = Column(Integer, default=0)
    duplicate_of = Column(Integer, ForeignKey("reports.id"), nullable=True)

    # Embedding stored as JSON string
    embedding = Column(Text, nullable=True)  # JSON array

    # Misc
    is_anonymous = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    reporter = relationship("User", back_populates="reports", foreign_keys=[reporter_id])
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    hypes = relationship("Hype", back_populates="report")
    status_logs = relationship("StatusLog", back_populates="report")
    verification = relationship("Verification", back_populates="report", uselist=False)
    notifications = relationship("Notification", back_populates="report")


class Hype(Base):
    __tablename__ = "hypes"
    __table_args__ = (UniqueConstraint("report_id", "user_id", name="unique_hype"),)

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    report = relationship("Report", back_populates="hypes")
    user = relationship("User", back_populates="hypes")


class StatusLog(Base):
    __tablename__ = "status_logs"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)
    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    report = relationship("Report", back_populates="status_logs")
    changer = relationship("User", foreign_keys=[changed_by])


class Verification(Base):
    __tablename__ = "verifications"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), unique=True, nullable=False)
    after_image_path = Column(String(500), nullable=False)
    verified_by_authority = Column(Integer, ForeignKey("users.id"), nullable=False)
    reporter_confirmed = Column(Boolean, nullable=True)  # None = pending
    ai_match_score = Column(Float, nullable=True)
    ai_same_location = Column(Boolean, nullable=True)
    ai_issue_resolved = Column(Boolean, nullable=True)
    flagged_for_review = Column(Boolean, default=False)
    # Feature 8: Enhanced quality rating fields
    ai_fix_quality = Column(String(20), nullable=True)       # excellent/good/temporary/inadequate
    ai_fix_quality_score = Column(Integer, nullable=True)    # 0-100
    ai_durability_risk = Column(String(10), nullable=True)   # low/medium/high
    ai_follow_up_days = Column(Integer, nullable=True)       # days until re-inspection
    ai_quality_reasoning = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    report = relationship("Report", back_populates="verification")
    authority = relationship("User", foreign_keys=[verified_by_authority])


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=True)
    message = Column(Text, nullable=False)
    channel = Column(String(50), default="in_app")  # in_app, email, sms
    sent_at = Column(DateTime, default=datetime.utcnow)
    read = Column(Boolean, default=False)

    user = relationship("User", back_populates="notifications")
    report = relationship("Report", back_populates="notifications")


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    building = Column(String(100), nullable=False)
    zone = Column(String(100), nullable=True)
    criticality = Column(Integer, default=3)  # 1-5
    plinth_area = Column(Float, nullable=True)  # Sq.m from official records
