"""NLP extraction service.

Converts a raw Slack message into a structured ProjectExtraction using
the LLM abstraction in services/llm.py.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import date, datetime
from typing import Optional

_MONTH_MAP = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}

def _coerce_date(value: str | None) -> str | None:
    """Convert a model date value to an ISO string, or return None."""
    if not value:
        return None
    # Already ISO
    if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        return value
    # Try common formats
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y",
                "%m/%d/%Y", "%m/%d/%y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date().isoformat()
        except ValueError:
            pass
    # "July 31st" / "31 July" style — strip ordinal suffixes first
    cleaned = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", value, flags=re.IGNORECASE)
    # "Month Day" or "Day Month" with optional year
    m = re.search(
        r"([A-Za-z]+)\s+(\d{1,2})(?:[,\s]+(\d{4}))?", cleaned
    )
    if m:
        month_str, day_str, year_str = m.group(1).lower(), m.group(2), m.group(3)
        month = _MONTH_MAP.get(month_str)
        if month:
            year = int(year_str) if year_str else date.today().year
            # If the resolved date is already in the past, assume next year
            try:
                resolved = date(year, month, int(day_str))
                if resolved < date.today() and not year_str:
                    resolved = date(year + 1, month, int(day_str))
                return resolved.isoformat()
            except ValueError:
                pass
    return None


from pydantic import BaseModel, field_validator

from services import llm

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Output schema
# ──────────────────────────────────────────────

class ProjectExtraction(BaseModel):
    project_name: str = ""
    customer: str = ""
    skills: list[str] = []
    timeline_start: Optional[str] = None  # ISO date string or null
    timeline_end: Optional[str] = None
    status: str = "Active"
    assignment_need: str = ""

    @field_validator("skills", mode="before")
    @classmethod
    def coerce_skills(cls, v: object) -> list[str]:
        if isinstance(v, str):
            return [s.strip() for s in re.split(r"[,;]", v) if s.strip()]
        if isinstance(v, list):
            return [str(s).strip() for s in v if s]
        return []


# ──────────────────────────────────────────────
# System prompt
# ──────────────────────────────────────────────

_SYSTEM_PROMPT = """You are a data extraction tool. A business manager sent the following Slack message to their team about a work assignment. Your job is to read the message and extract structured data from it.

You are NOT being asked to do the work. You are NOT the recipient. You are a tool that reads messages and returns JSON.

Return ONLY this JSON object. No explanation, no commentary, no markdown:

{"project_name":"","customer":"","skills":[],"timeline_start":null,"timeline_end":null,"status":"Active","assignment_need":""}

Field rules:
- project_name: short name for the project (e.g. "IBM Web App Pipeline", "MongoDB Chatbot")
- customer: the company or client being served (e.g. "IBM", "MongoDB", "NVDA", "ABC Corp")
- skills: array of technical skills or products mentioned (e.g. ["Python","Kubernetes"])
- timeline_start: ISO date YYYY-MM-DD if an explicit start date is mentioned, otherwise null
- timeline_end: ISO date YYYY-MM-DD for any deadline ("by X", "due X", "before X"), otherwise null
- status: exactly one of: Active, In Progress, On Hold, Completed, Cancelled — default Active
- assignment_need: one sentence describing what work is needed

Date rules:
- "by <date>", "due <date>", "before <date>" → timeline_end only
- "starting <date>", "from <date>" → timeline_start only

If a value cannot be determined, use "" for strings, [] for arrays, null for dates.
"""

# ──────────────────────────────────────────────
# Public extraction function
# ──────────────────────────────────────────────

def _scrub_mentions(text: str) -> str:
    """Remove @Name mentions and second-person address phrasing so local
    models don't roleplay the message instead of extracting JSON."""
    # Remove @mentions
    text = re.sub(r"@[A-Za-z][A-Za-z0-9_.\-]*", "", text)
    # Remove leading "I need you to", "Hey, I need you to", "Please", etc.
    text = re.sub(
        r"^(hey[\s,]*)?i\s+need\s+you\s+to\s+",
        "",
        text.strip(),
        flags=re.IGNORECASE,
    )
    text = re.sub(r"^(hey[\s,]*)?please\s+", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"^hey[\s,]+", "", text.strip(), flags=re.IGNORECASE)
    return text.strip()


# Month names to exclude from noun extraction
_MONTHS = {"January","February","March","April","May","June","July","August",
           "September","October","November","December",
           "Jan","Feb","Mar","Apr","Jun","Jul","Aug","Sep","Oct","Nov","Dec"}
_SKIP_NOUNS = {"I","We","The","A","An","Hey","Hi","Need","Needs",
               "Looking","Please","Urgently","ASAP","Sure","Ok","Hello"} | _MONTHS


def _extract_first_noun(text: str) -> str:
    """Heuristic: return the first capitalised word that looks like a company/product name.
    Prefers words that appear after 'for/from/at' (typically the client name).
    Excludes month names and common filler words.
    """
    # Prefer: "for IBM", "at MongoDB", "from NVDA" — explicit client references
    m = re.search(
        r"(?:for|from|at)\s+([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)*)",
        text,
    )
    if m:
        candidate = m.group(1).strip()
        first_word = candidate.split()[0]
        if first_word not in _SKIP_NOUNS:
            return candidate
    # Fallback: first capitalised word in the sentence that isn't a skip word
    for word in re.findall(r"\b[A-Z][A-Za-z0-9]+\b", text):
        if word not in _SKIP_NOUNS:
            return word
    return ""


def extract_from_message(text: str) -> ProjectExtraction:
    """Extract structured project fields from a Slack message string.

    Returns a ProjectExtraction. Never raises — on any failure returns an
    empty extraction so the caller can handle gracefully.
    """
    try:
        # Strip @mentions and command phrasing so local models don't roleplay
        clean_text = _scrub_mentions(text)
        # Prefix as a third-person statement so qwen doesn't treat it as a command
        prompt_text = f"Assignment request: {clean_text}"
        raw = llm.complete(_SYSTEM_PROMPT, prompt_text)
        # Strip markdown code fences if the model wraps output despite instructions
        raw = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw.strip())
        # Normalise fullwidth punctuation some models emit (e.g. qwen with CJK locale)
        raw = raw.replace("，", ",").replace("：", ":").replace("。", ".").replace(""", '"').replace(""", '"')
        # Some local models emit trailing commas — strip them before parsing
        raw = re.sub(r",\s*([}\]])", r"\1", raw)
        # Extract first complete JSON object if model prepends/appends prose.
        # Find the outermost { ... } by tracking brace depth.
        start = raw.find("{")
        if start != -1:
            depth = 0
            end = start
            for i, ch in enumerate(raw[start:], start):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            raw = raw[start : end + 1]
        data = json.loads(raw)
        # Normalise keys: some local models inject spaces into key names,
        # e.g. "timeline_ end" → "timeline_end" (collapse runs of underscores/spaces)
        def _norm_key(k: str) -> str:
            k = k.replace(" ", "_")
            return re.sub(r"_+", "_", k).strip("_")
        data = {_norm_key(k): v for k, v in data.items()}
        extraction = ProjectExtraction(**data)
        # Coerce date fields — model may return natural language instead of ISO
        extraction.timeline_start = _coerce_date(extraction.timeline_start)
        extraction.timeline_end = _coerce_date(extraction.timeline_end)
        # Validate status is one of the allowed values; reset to Active if not
        _VALID_STATUSES = {"Active", "In Progress", "On Hold", "Completed", "Cancelled"}
        if extraction.status not in _VALID_STATUSES:
            extraction.status = "Active"
        # Default timeline_start to today if the model left it null
        if not extraction.timeline_start:
            extraction.timeline_start = date.today().isoformat()
        # Synthesise a customer from text heuristics if the model left it blank
        if not extraction.customer:
            extraction.customer = _extract_first_noun(clean_text)
        # Synthesise a project name if the model left it blank
        if not extraction.project_name:
            parts = []
            if extraction.customer:
                parts.append(extraction.customer)
            if extraction.skills:
                parts.append(extraction.skills[0])
            if parts:
                extraction.project_name = " – ".join(parts)
            elif clean_text:
                # Last resort: truncated message text as the name
                extraction.project_name = clean_text[:60].rstrip()
        return extraction
    except Exception as exc:
        logger.error("NLP extraction failed for text '%s...': %s", text[:80], exc)
        return ProjectExtraction()
