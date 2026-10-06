from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from datetime import datetime
from app.models import UserRole, ReportStatus


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.student
    department: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    department: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ── Location ──────────────────────────────────────────────────────────────────

class LocationOut(BaseModel):
    id: int
    building: str
    zone: Optional[str] = None
    criticality: int
    plinth_area: Optional[float] = None

    class Config:
        from_attributes = True


# ── Report ────────────────────────────────────────────────────────────────────

class AIResult(BaseModel):
    hazard_type: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[int] = None
    is_safety_critical: bool = False
    summary: Optional[str] = None
    reasoning: Optional[str] = None
    confidence: Optional[float] = None


class PriorityBreakdown(BaseModel):
    severity_norm: float
    hype_norm: float
    recurrence_norm: float
    location_criticality_norm: float
    age_bonus: float
    final_score: float
    safety_critical_override: bool


class StatusLogOut(BaseModel):
    id: int
    old_status: Optional[str] = None
    new_status: str
    note: Optional[str] = None
    created_at: datetime
    changer_name: Optional[str] = None

    class Config:
        from_attributes = True


class ReportOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    image_path: Optional[str] = None
    building: str
    zone: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    hazard_type: Optional[str] = None
    category: Optional[str] = None
    service_id: Optional[str] = None
    severity: Optional[int] = None
    is_safety_critical: bool = False
    ai_summary: Optional[str] = None
    ai_reasoning: Optional[str] = None
    ai_confidence: Optional[float] = None
    ml_severity: Optional[int] = None
    ml_severity_confidence: Optional[float] = None
    ml_model: Optional[str] = None
    status: ReportStatus
    assigned_department: Optional[str] = None
    priority_score: float = 0.0
    hype_count: int = 0
    recurrence_count: int = 0
    duplicate_of: Optional[int] = None
    is_anonymous: bool = False
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    # Hydrated fields (set by endpoint)
    reporter_name: Optional[str] = None
    reporter_id: Optional[int] = None
    current_user_hyped: bool = False
    status_history: List[StatusLogOut] = []
    priority_breakdown: Optional[PriorityBreakdown] = None
    verification: Optional[Any] = None

    class Config:
        from_attributes = True


class ReportListItem(BaseModel):
    id: int
    title: str
    building: str
    zone: Optional[str] = None
    hazard_type: Optional[str] = None
    category: Optional[str] = None
    service_id: Optional[str] = None
    severity: Optional[int] = None
    is_safety_critical: bool = False
    status: ReportStatus
    priority_score: float = 0.0
    hype_count: int = 0
    recurrence_count: int = 0
    is_anonymous: bool = False
    created_at: datetime
    reporter_name: Optional[str] = None
    current_user_hyped: bool = False
    image_path: Optional[str] = None

    class Config:
        from_attributes = True


class PaginatedReports(BaseModel):
    items: List[ReportListItem]
    total: int
    page: int
    page_size: int
    pages: int


# ── Status update ─────────────────────────────────────────────────────────────

class StatusUpdate(BaseModel):
    status: ReportStatus
    note: Optional[str] = None


class AssignUpdate(BaseModel):
    assigned_to: int
    note: Optional[str] = None


# ── Hype ──────────────────────────────────────────────────────────────────────

class HypeOut(BaseModel):
    report_id: int
    hype_count: int
    current_user_hyped: bool


# ── Duplicate ─────────────────────────────────────────────────────────────────

class DuplicateResult(BaseModel):
    status: str  # DUPLICATE | POSSIBLE_DUPLICATE | UNIQUE | RECURRING
    duplicate_of: Optional[int] = None
    suggestions: List[dict] = []
    recurrence_count: int = 0
    message: Optional[str] = None


# ── Verification ─────────────────────────────────────────────────────────────

class VerificationOut(BaseModel):
    id: int
    after_image_path: str
    reporter_confirmed: Optional[bool] = None
    ai_match_score: Optional[float] = None
    ai_same_location: Optional[bool] = None
    ai_issue_resolved: Optional[bool] = None
    flagged_for_review: bool = False
    ai_fix_quality: Optional[str] = None
    ai_fix_quality_score: Optional[int] = None
    ai_durability_risk: Optional[str] = None
    ai_follow_up_days: Optional[int] = None
    ai_quality_reasoning: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationOut(BaseModel):
    id: int
    report_id: Optional[int] = None
    message: str
    channel: str
    sent_at: datetime
    read: bool

    class Config:
        from_attributes = True


# ── Analytics ─────────────────────────────────────────────────────────────────

class AnalyticsSummary(BaseModel):
    total_reports: int
    open_reports: int
    resolved_reports: int
    avg_resolution_hours: Optional[float]
    median_resolution_hours: Optional[float]
    duplicate_percentage: float
    critical_open: int
    by_status: dict
    by_category: dict
    top_buildings: List[dict]
    recurring_issues: List[dict]
    reports_per_day: List[dict]
    hype_leaderboard: List[dict]
    resolution_by_department: List[dict]
