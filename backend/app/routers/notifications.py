from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Notification, User
from app.schemas import NotificationOut
from app.routers.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=List[NotificationOut])
def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.sent_at.desc()).limit(50).all()


@router.patch("/read")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.read == False
    ).update({"read": True})
    db.commit()
    return {"message": "All notifications marked as read"}


@router.patch("/{notif_id}/read")
def mark_read(
    notif_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notif = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.user_id == current_user.id
    ).first()
    if notif:
        notif.read = True
        db.commit()
    return {"message": "Marked as read"}
