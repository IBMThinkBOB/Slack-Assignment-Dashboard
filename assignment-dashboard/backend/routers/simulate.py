"""Slack message simulator endpoints.

Provides:
  POST /slack/simulate       — send a message (any role), run the full pipeline
  GET  /slack/messages       — list all simulator messages sorted by created_at
  POST /slack/claim/{event_id} — user claims an unassigned project
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.assignment import Assignment
from models.resource import Resource
from models.slack_event import SlackEvent
from services.correlation import process_slack_event

router = APIRouter()

# ── Affirmative intent detection ───────────────────────────────────────────────

_AFFIRMATIVE = re.compile(
    r"\b("
    r"yes|yeah|yep|sure|ok|okay|done|got\s*it|on\s*it"
    r"|i'?ll\s*(do|take|handle|pick\s*up|cover)\s*(it|this|that)?"
    r"|i('m|\s+am)\s+(on|taking|handling|picking\s+up|doing)\s*(it|this|that)?"
    r"|sounds?\s*(good|great|fine|like\s+a\s+plan)"
    r"|count\s+me\s+in"
    r"|assign\s+it\s+to\s+me"
    r"|happy\s+to\s+(help|do\s+it|take\s+(it|this))"
    r"|claim(ing|ed)?"
    r"|i\s+(can|will)\s+(do|help|take|handle|cover)\s*(it|this|that|this\s+project)?"
    r")\b",
    re.IGNORECASE,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _extract_mention(text: str) -> str | None:
    m = re.search(r"@([A-Za-z][A-Za-z0-9_.\-]*)", text)
    return m.group(1) if m else None


def _find_resource_by_name(name: str, db: Session) -> Resource | None:
    name_lower = name.lower().strip()
    for r in db.query(Resource).all():
        if r.name.lower().strip().startswith(name_lower):
            return r
    return None


def _find_or_create_resource(name: str, db: Session) -> Resource:
    existing = _find_resource_by_name(name, db)
    if existing:
        return existing
    r = Resource(name=name.strip(), availability="Available", utilization=0.0)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def _ensure_assignment(project_id: str, resource_id: str, role: str | None, db: Session) -> Assignment:
    existing = (
        db.query(Assignment)
        .filter(Assignment.project_id == project_id, Assignment.resource_id == resource_id)
        .first()
    )
    if existing:
        return existing
    a = Assignment(
        project_id=project_id,
        resource_id=resource_id,
        role=role or "Team Member",
        status="Assigned",
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


def _last_unclaimed_event(sender: str, db: Session) -> SlackEvent | None:
    """Most recent simulator message that has a project, is unclaimed,
    and was NOT sent by `sender` — i.e. the last message a different person posted.
    """
    return (
        db.query(SlackEvent)
        .filter(
            SlackEvent.channel == "simulator",
            SlackEvent.project_id.isnot(None),
            SlackEvent.claimed_by_resource_id.is_(None),
            SlackEvent.is_system_msg.is_(False),
            SlackEvent.slack_user_id != sender,
        )
        .order_by(SlackEvent.created_at.desc())
        .first()
    )


def _post_system_message(text: str, project_id: str | None, resource_id: str | None, db: Session) -> SlackEvent:
    """Insert an auto-generated system confirmation message into the thread."""
    msg = SlackEvent(
        channel="simulator",
        slack_user_id="System",
        text=text,
        ts=None,
        processed=True,
        is_system_msg=True,
        project_id=project_id,
        claimed_by_resource_id=resource_id,
        created_at=_now(),
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def _serialize_event(event: SlackEvent) -> dict:
    project = event.project
    claimed = event.claimed_by
    return {
        "event_id": event.event_id,
        "text": event.text,
        "sender": event.slack_user_id or "Admin",
        "created_at": event.created_at.isoformat() if event.created_at else None,
        "is_system_msg": event.is_system_msg or False,
        "project_id": project.project_id if project else None,
        "project_name": project.name if project else None,
        "customer": project.customer if project else None,
        "skills": project.required_skills or [] if project else [],
        "status": project.status if project else None,
        "mentioned_name": event.mentioned_name,
        "claimed_by_resource_id": event.claimed_by_resource_id,
        "claimed_by_name": claimed.name if claimed else None,
    }


# ── Schemas ────────────────────────────────────────────────────────────────────

class SimulateRequest(BaseModel):
    text: str
    channel: str = "simulator"
    user: str = "Admin"
    # If set, this reply is explicitly targeted at a specific message's project
    reply_to_event_id: str | None = None


class ClaimRequest(BaseModel):
    resource_id: str | None = None
    name: str | None = None
    role: str | None = None


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/messages", tags=["Slack"])
def list_messages(db: Session = Depends(get_db)) -> list[dict]:
    """Return all simulator messages sorted chronologically by created_at."""
    events = (
        db.query(SlackEvent)
        .filter(SlackEvent.channel == "simulator")
        .order_by(SlackEvent.created_at.asc())
        .all()
    )
    return [_serialize_event(e) for e in events]


@router.post("/simulate", tags=["Slack"])
def simulate_slack_message(
    body: SimulateRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Simulate a Slack message from any user.

    Admin messages: run the full NLP pipeline.  If an @mention matches a
    known resource, auto-assign and emit a system confirmation message.

    User messages:
      - If reply_to_event_id is set, claim that specific message's project.
      - Otherwise if text is affirmative, claim the most recent unclaimed
        message that was sent by someone else.
    """
    is_admin_msg = body.user.lower() in ("admin", "")
    mentioned_name = _extract_mention(body.text) if is_admin_msg else None

    event = SlackEvent(
        channel=body.channel,
        slack_user_id=body.user,
        text=body.text.strip(),
        ts=None,
        processed=not is_admin_msg,
        mentioned_name=mentioned_name,
        created_at=_now(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    if is_admin_msg:
        process_slack_event(event.event_id)
        db.refresh(event)

        if mentioned_name and event.project_id:
            resource = _find_resource_by_name(mentioned_name, db)
            if resource:
                _ensure_assignment(event.project_id, resource.resource_id, None, db)
                event.claimed_by_resource_id = resource.resource_id
                db.commit()
                db.refresh(event)
                _post_system_message(
                    f"✅ {resource.name} has been assigned to {event.project.name}",
                    event.project_id,
                    resource.resource_id,
                    db,
                )
    else:
        # Determine which message this reply targets
        target: SlackEvent | None = None

        if body.reply_to_event_id:
            # Explicit reply — find that specific message
            target = (
                db.query(SlackEvent)
                .filter(
                    SlackEvent.event_id == body.reply_to_event_id,
                    SlackEvent.project_id.isnot(None),
                    SlackEvent.claimed_by_resource_id.is_(None),
                )
                .first()
            )
        elif _AFFIRMATIVE.search(body.text):
            # Affirmative with no explicit target — find the most recent
            # unclaimed message from someone else
            target = _last_unclaimed_event(body.user, db)

        if target:
            resource = _find_or_create_resource(body.user, db)
            _ensure_assignment(target.project_id, resource.resource_id, None, db)
            target.claimed_by_resource_id = resource.resource_id
            event.project_id = target.project_id
            event.claimed_by_resource_id = resource.resource_id
            db.commit()
            db.refresh(event)
            _post_system_message(
                f"✅ {resource.name} claimed {target.project.name}",
                target.project_id,
                resource.resource_id,
                db,
            )

    return _serialize_event(event)


@router.post("/claim/{event_id}", tags=["Slack"])
def claim_message(
    event_id: str,
    body: ClaimRequest,
    db: Session = Depends(get_db),
) -> dict:
    """User claims an unassigned project via the Claim button.

    Accepts resource_id (existing) or name (find-or-create).
    Creates an Assignment, marks the event claimed, and emits a system message.
    """
    event = db.query(SlackEvent).filter(SlackEvent.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Message not found")
    if not event.project_id:
        raise HTTPException(status_code=400, detail="This message has no linked project yet")
    if event.claimed_by_resource_id:
        raise HTTPException(status_code=409, detail="Already claimed")

    if body.resource_id:
        resource = db.query(Resource).filter(Resource.resource_id == body.resource_id).first()
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")
    elif body.name:
        resource = _find_or_create_resource(body.name, db)
    else:
        raise HTTPException(status_code=422, detail="Provide resource_id or name")

    _ensure_assignment(event.project_id, resource.resource_id, body.role, db)
    event.claimed_by_resource_id = resource.resource_id
    db.commit()
    db.refresh(event)

    # AC9 — system confirmation message
    _post_system_message(
        f"✅ {resource.name} claimed {event.project.name}",
        event.project_id,
        resource.resource_id,
        db,
    )

    return _serialize_event(event)
