"""OpenAI-compatible LLM client abstraction.

All vendor-specific details are isolated here. Switching providers only
requires changing three env vars: LLM_BASE_URL, LLM_API_KEY, LLM_MODEL.

BOB_API_KEY in .env maps to LLM_API_KEY via config.py.

For watsonx/BOB: the API key is exchanged for a short-lived IAM Bearer token
automatically. The token is cached and refreshed when it expires.
"""
from __future__ import annotations

import logging
import time

import httpx
from openai import OpenAI

from config import settings

logger = logging.getLogger(__name__)

# ── IAM token cache ───────────────────────────────────────────────────────────

_iam_token: str | None = None
_iam_expires_at: float = 0.0
_IAM_URL = "https://iam.cloud.ibm.com/identity/token"
# Refresh 5 minutes before expiry
_IAM_REFRESH_BUFFER = 300


def _is_watsonx() -> bool:
    """True when the base URL points to IBM Cloud (watsonx / BOB)."""
    return "ibm.com" in settings.llm_base_url or "watsonx" in settings.llm_base_url


def _get_iam_token() -> str:
    """Exchange the IBM API key for a Bearer token, with caching."""
    global _iam_token, _iam_expires_at
    if _iam_token and time.time() < _iam_expires_at - _IAM_REFRESH_BUFFER:
        return _iam_token
    resp = httpx.post(
        _IAM_URL,
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": settings.llm_api_key,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    resp.raise_for_status()
    payload = resp.json()
    _iam_token = payload["access_token"]
    _iam_expires_at = time.time() + int(payload.get("expires_in", 3600))
    logger.debug("Refreshed IAM token, expires in %ss", payload.get("expires_in"))
    return _iam_token


# ── Client factory ────────────────────────────────────────────────────────────

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _is_watsonx():
        # Always build a fresh client so it picks up a refreshed IAM token
        token = _get_iam_token()
        return OpenAI(
            base_url=settings.llm_base_url,
            api_key=token,
        )
    if _client is None:
        _client = OpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
        )
    return _client


def complete(system_prompt: str, user_message: str) -> str:
    """Send a chat completion request and return the assistant content string.

    Args:
        system_prompt: Instructions for the model (e.g. "Return JSON only").
        user_message: The user-turn content (e.g. a Slack message).

    Returns:
        The raw string from the model's first choice.
    """
    client = _get_client()
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0,
    )
    content = response.choices[0].message.content or ""
    logger.debug("LLM response (%d chars): %s", len(content), content[:200])
    return content
