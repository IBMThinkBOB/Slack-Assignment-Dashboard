"""Resources CRUD router."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from middleware.role_guard import require_admin
from models.resource import Resource

router = APIRouter()


class ResourceCreate(BaseModel):
    name: str
    email: Optional[str] = None
    availability: str = "Available"
    utilization: float = 0.0


class ResourceUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    availability: Optional[str] = None
    utilization: Optional[float] = None


def _serialize(r: Resource) -> dict:
    return {
        "resource_id": r.resource_id,
        "name": r.name,
        "email": r.email,
        "availability": r.availability,
        "utilization": r.utilization,
    }


@router.get("")
def list_resources(db: Session = Depends(get_db)) -> list[dict]:
    return [_serialize(r) for r in db.query(Resource).order_by(Resource.name).all()]


@router.get("/{resource_id}")
def get_resource(resource_id: str, db: Session = Depends(get_db)) -> dict:
    r = db.query(Resource).filter(Resource.resource_id == resource_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Resource not found")
    return _serialize(r)


@router.post("", status_code=201)
def create_resource(
    body: ResourceCreate,
    db: Session = Depends(get_db),
    _role: str = Depends(require_admin),
) -> dict:
    resource = Resource(**body.model_dump())
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return _serialize(resource)


@router.put("/{resource_id}")
def update_resource(
    resource_id: str,
    body: ResourceUpdate,
    db: Session = Depends(get_db),
    _role: str = Depends(require_admin),
) -> dict:
    r = db.query(Resource).filter(Resource.resource_id == resource_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Resource not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(r, field, value)
    db.commit()
    db.refresh(r)
    return _serialize(r)


@router.delete("/{resource_id}")
def delete_resource(
    resource_id: str,
    db: Session = Depends(get_db),
    _role: str = Depends(require_admin),
) -> Response:
    r = db.query(Resource).filter(Resource.resource_id == resource_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Resource not found")
    db.delete(r)
    db.commit()
    return Response(status_code=204)
