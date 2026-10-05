from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Location
from app.schemas import LocationOut
from app.routers.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("", response_model=List[LocationOut])
def list_locations(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Location).order_by(Location.building).all()
