"""
School routes — create & list schools.
Governance roles only. Mounted under /api/v1/schools.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.dependencies import require_roles, get_current_user
from core.roles import Role
from database.db import get_db
from database.models import School, User
from governance.schemas import SchoolCreate, SchoolOut

router = APIRouter(prefix="/schools", tags=["Schools"])


@router.post(
    "",
    response_model=SchoolOut,
    dependencies=[Depends(require_roles(Role.DEO, Role.MEO, Role.BEO))],
)
def create_school(data: SchoolCreate, db: Session = Depends(get_db)):
    """Register a new school (governance officers only)."""
    school = School(**data.model_dump())
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


@router.get("", response_model=List[SchoolOut])
def list_schools(
    district: Optional[str] = Query(None),
    mandal: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List schools, optionally filtered by district/mandal."""
    q = db.query(School)
    if district:
        q = q.filter(School.district == district)
    if mandal:
        q = q.filter(School.mandal == mandal)
    return q.all()
