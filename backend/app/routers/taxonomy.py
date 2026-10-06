"""
GET /taxonomy  — returns the full 24-department / sub-service hierarchy.
Used by the frontend New Report stepper to build the category picker.
"""
from fastapi import APIRouter
from app.core.taxonomy import DEPARTMENTS

router = APIRouter(prefix="/taxonomy", tags=["taxonomy"])


@router.get("")
def get_taxonomy():
    """Return the full department + sub-service hierarchy."""
    return {"departments": DEPARTMENTS}
