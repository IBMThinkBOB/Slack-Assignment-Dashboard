"""Projects CRUD router."""
from __future__ import annotations

from typing import Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from middleware.role_guard import require_admin
from models.project import Project

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str
    customer: str
    status: str = "Active"
    type: Optional[str] = None
    priority: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    progress_percent: int = 0
    description: Optional[str] = None
    required_skills: Optional[list[str]] = None
    manager: Optional[str] = None
    practice: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    customer: Optional[str] = None
    status: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    progress_percent: Optional[int] = None
    description: Optional[str] = None
    required_skills: Optional[list[str]] = None
    manager: Optional[str] = None
    practice: Optional[str] = None


def _serialize(p: Project, include_assignments: bool = False) -> dict:
    # Derive "Assigned To" from the first active assignment on this project
    active_assignments = [a for a in p.assignments if a.status != "Removed"]
    if active_assignments:
        assigned_to = ", ".join(
            a.resource.name for a in active_assignments if a.resource
        ) or "Unassigned"
    else:
        assigned_to = "Unassigned"

    data = {
        "project_id": p.project_id,
        "name": p.name,
        "customer": p.customer,
        "status": p.status,
        "type": p.type,
        "priority": p.priority,
        "start_date": str(p.start_date) if p.start_date else None,
        "end_date": str(p.end_date) if p.end_date else None,
        "progress_percent": p.progress_percent,
        "description": p.description,
        "source": p.source,
        "required_skills": p.required_skills or [],
        "manager": p.manager,
        "practice": p.practice,
        "assigned_to": assigned_to,
    }
    if include_assignments:
        data["assignments"] = [
            {
                "assignment_id": a.assignment_id,
                "resource_id": a.resource_id,
                "resource_name": a.resource.name if a.resource else None,
                "role": a.role,
                "status": a.status,
                "progress_percent": a.progress_percent,
            }
            for a in p.assignments
        ]
    return data


# ── Endpoints ─────────────────────────────────────────────

@router.get("")
def list_projects(
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    customer: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> list[dict]:
    q = db.query(Project)
    if status:
        q = q.filter(Project.status == status)
    if type:
        q = q.filter(Project.type == type)
    if customer:
        q = q.filter(Project.customer.ilike(f"%{customer}%"))
    return [_serialize(p) for p in q.order_by(Project.name).all()]


@router.get("/{project_id}")
def get_project(project_id: str, db: Session = Depends(get_db)) -> dict:
    p = db.query(Project).filter(Project.project_id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return _serialize(p, include_assignments=True)


@router.post("", status_code=201)
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    _role: str = Depends(require_admin),
) -> dict:
    project = Project(**body.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return _serialize(project)


@router.put("/{project_id}")
def update_project(
    project_id: str,
    body: ProjectUpdate,
    db: Session = Depends(get_db),
    _role: str = Depends(require_admin),
) -> dict:
    p = db.query(Project).filter(Project.project_id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(p, field, value)
    db.commit()
    db.refresh(p)
    return _serialize(p)


@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    _role: str = Depends(require_admin),
) -> Response:
    p = db.query(Project).filter(Project.project_id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(p)
    db.commit()
    return Response(status_code=204)
