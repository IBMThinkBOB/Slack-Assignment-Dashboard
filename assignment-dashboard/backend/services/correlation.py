"""Correlation service.

Takes a ProjectExtraction and upserts a Project record in the database.
Also called by the Slack router background task.
"""
from __future__ import annotations

import logging
from datetime import date

from sqlalchemy.orm import Session

from database import SessionLocal
from models.project import Project
from models.slack_event import SlackEvent
from services.nlp import extract_from_message

logger = logging.getLogger(__name__)


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def upsert_project_from_extraction(extraction, source: str, db: Session) -> Project:
    """Upsert a Project from a ProjectExtraction. Match key: (name, customer)."""
    name = (extraction.project_name or "").strip()
    customer = (extraction.customer or "").strip()

    # Need at least a name to create a meaningful project record
    if not name:
        logger.warning("Extraction produced no project_name — skipping upsert")
        return None

    existing = (
        db.query(Project)
        .filter(Project.name == name, Project.customer == customer)
        .first()
    )

    if existing:
        # Update fields that have new information
        if extraction.skills:
            existing.required_skills = extraction.skills
        if extraction.status:
            _set_status(existing, extraction.status)
        if extraction.timeline_start:
            existing.start_date = _parse_date(extraction.timeline_start)
        if extraction.timeline_end:
            existing.end_date = _parse_date(extraction.timeline_end)
        db.commit()
        db.refresh(existing)
        logger.info("Updated existing project %s (%s)", existing.project_id, existing.name)
        return existing
    else:
        project = Project(
            name=name,
            customer=customer,
            status=_normalize_status(extraction.status),
            source=source,
            required_skills=extraction.skills or [],
            start_date=_parse_date(extraction.timeline_start),
            end_date=_parse_date(extraction.timeline_end),
            description=extraction.assignment_need or "",
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        logger.info("Created new project %s (%s) from %s", project.project_id, project.name, source)
        return project


def _normalize_status(raw: str) -> str:
    mapping = {
        "active": "Active",
        "in progress": "In Progress",
        "on hold": "On Hold",
        "completed": "Completed",
        "cancelled": "Cancelled",
    }
    return mapping.get((raw or "").lower(), "Active")


def _set_status(project: Project, raw: str) -> None:
    project.status = _normalize_status(raw)


def process_slack_event(event_id: str) -> None:
    """Background task: load SlackEvent by ID, extract, upsert project, mark processed.

    Opens its own DB session since this runs outside the request lifecycle.
    """
    db: Session = SessionLocal()
    try:
        event = db.query(SlackEvent).filter(SlackEvent.event_id == event_id).first()
        if not event:
            logger.warning("SlackEvent %s not found", event_id)
            return

        extraction = extract_from_message(event.text)
        project = upsert_project_from_extraction(extraction, source="slack", db=db)

        # Only mark processed=True when we actually created/updated a project record
        if project:
            event.processed = True
            event.project_id = project.project_id
        db.commit()
        logger.info("Processed SlackEvent %s → project %s", event_id, project.project_id if project else None)
    except Exception as exc:
        db.rollback()
        logger.error("process_slack_event(%s) failed: %s", event_id, exc)
    finally:
        db.close()
