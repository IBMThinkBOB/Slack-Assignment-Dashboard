"""Assignments CRUD router."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from middleware.role_guard import require_admin
from models.assignment import Assignment
from models.project import Project
from models.resource import Resource

router = APIRouter()


class AssignmentCreate(BaseModel):
    project_id: str
    resource_id: str
    role: Optional[str] = None
    status: str = "Assigned"
    progress_percent: int = 0


class AssignmentUpdate(BaseModel):
    resource_id: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    progress_percent: Optional[int] = None


def _serialize(a: Assignment) -> dict:
    return {
        "assignment_id": a.assignment_id,
        "project_id": a.project_id,
        "project_name": a.project.name if a.project else None,
        "resource_id": a.resource_id,
        "resource_name": a.resource.name if a.resource else None,
        "role": a.role,
        "status": a.status,
        "progress_percent": a.progress_percent,
    }


@router.get("")
def list_assignments(
    project_id: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> list[dict]:
    q = db.query(Assignment)
    if project_id:
        q = q.filter(Assignment.project_id == project_id)
    if resource_id:
        q = q.filter(Assignment.resource_id == resource_id)
    return [_serialize(a) for a in q.all()]


@router.get("/{assignment_id}")
def get_assignment(assignment_id: str, db: Session = Depends(get_db)) -> dict:
    a = db.query(Assignment).filter(Assignment.assignment_id == assignment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return _serialize(a)


@router.post("", status_code=201)
def create_assignment(
    body: AssignmentCreate,
    db: Session = Depends(get_db),
    _role: str = Depends(require_admin),
) -> dict:
    # Validate FK references exist
    if not db.query(Project).filter(Project.project_id == body.project_id).first():
        raise HTTPException(status_code=404, detail="Project not found")
    if not db.query(Resource).filter(Resource.resource_id == body.resource_id).first():
        raise HTTPException(status_code=404, detail="Resource not found")

    assignment = Assignment(**body.model_dump())
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return _serialize(assignment)


@router.put("/{assignment_id}")
def update_assignment(
    assignment_id: str,
    body: AssignmentUpdate,
    x_role: str = Query(default="user"),
    db: Session = Depends(get_db),
) -> dict:
    """Admins can update any field. Users can update status and progress_percent only."""
    a = db.query(Assignment).filter(Assignment.assignment_id == assignment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assignment not found")

    updates = body.model_dump(exclude_none=True)

    if x_role.lower() != "admin":
        # Non-admins can only update their own progress/status
        allowed = {"status", "progress_percent"}
        disallowed = set(updates.keys()) - allowed
        if disallowed:
            raise HTTPException(
                status_code=403,
                detail=f"Users may only update: {sorted(allowed)}",
            )

    for field, value in updates.items():
        setattr(a, field, value)

    db.commit()
    db.refresh(a)
    return _serialize(a)


@router.delete("/{assignment_id}")
def delete_assignment(
    assignment_id: str,
    db: Session = Depends(get_db),
    _role: str = Depends(require_admin),
) -> Response:
    a = db.query(Assignment).filter(Assignment.assignment_id == assignment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assignment not found")
    db.delete(a)
    db.commit()
    return Response(status_code=204)
