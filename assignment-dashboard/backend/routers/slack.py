import hashlib
import hmac
import logging
import time
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from database import get_db
from middleware.role_guard import require_admin
from models.slack_event import SlackEvent

logger = logging.getLogger(__name__)

router = APIRouter()


# ──────────────────────────────────────────────
# Slack signature verification
# ──────────────────────────────────────────────

def _verify_slack_signature(request_body: bytes, timestamp: str, signature: str, signing_secret: str) -> bool:
    """Return True if the Slack signature is valid."""
    base = f"v0:{timestamp}:{request_body.decode('utf-8')}"
    expected = "v0=" + hmac.new(
        signing_secret.encode("utf-8"),
        base.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()  # hmac.new is the correct stdlib call
    return hmac.compare_digest(expected, signature)


# ──────────────────────────────────────────────
# Background extraction task (imported lazily to avoid circular)
# ──────────────────────────────────────────────

def _run_extraction(event_id: str) -> None:
    """Triggered in background after a Slack event is stored."""
    from services.correlation import process_slack_event  # lazy import — avoids circular at startup
    try:
        process_slack_event(event_id)
    except Exception as exc:
        logger.error("Background extraction failed for event %s: %s", event_id, exc)


# ──────────────────────────────────────────────
# POST /slack/events  — Slack Events API endpoint
# ──────────────────────────────────────────────

@router.post("/events")
async def slack_events(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Any:
    from config import settings  # local import keeps startup clean

    body = await request.body()

    # ── Signature verification ──
    if settings.slack_signing_secret:
        timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
        signature = request.headers.get("X-Slack-Signature", "")

        # Reject replays older than 5 minutes
        if abs(time.time() - float(timestamp or 0)) > 300:
            raise HTTPException(status_code=403, detail="Request timestamp too old")

        if not _verify_slack_signature(body, timestamp, signature, settings.slack_signing_secret):
            raise HTTPException(status_code=403, detail="Invalid Slack signature")

    payload: dict = await request.json() if not body else __import__("json").loads(body)

    # ── URL verification challenge (required when first setting up the app) ──
    if payload.get("type") == "url_verification":
        return {"challenge": payload["challenge"]}

    # ── Handle event callbacks ──
    event = payload.get("event", {})
    event_type = event.get("type", "")

    # Only process user messages — ignore bot messages and sub-types like joins
    if event_type == "message" and not event.get("bot_id") and not event.get("subtype"):
        text = event.get("text", "").strip()
        if text:
            slack_event = SlackEvent(
                channel=event.get("channel"),
                slack_user_id=event.get("user"),
                text=text,
                ts=event.get("ts"),
                processed=False,
            )
            db.add(slack_event)
            db.commit()
            db.refresh(slack_event)
            logger.info("Stored Slack event %s from channel %s", slack_event.event_id, slack_event.channel)

            background_tasks.add_task(_run_extraction, slack_event.event_id)

    return Response(status_code=200)


# ──────────────────────────────────────────────
# GET /slack/events  — list recent raw events (admin debug)
# ──────────────────────────────────────────────

@router.get("/events")
def list_slack_events(
    limit: int = 50,
    db: Session = Depends(get_db),
    _role: str = Depends(require_admin),
) -> list[dict]:
    events = (
        db.query(SlackEvent)
        .order_by(SlackEvent.ts.desc().nullslast())
        .limit(limit)
        .all()
    )
    return [
        {
            "event_id": e.event_id,
            "channel": e.channel,
            "slack_user_id": e.slack_user_id,
            "text": e.text,
            "ts": e.ts,
            "processed": e.processed,
            "project_id": e.project_id,
        }
        for e in events
    ]
