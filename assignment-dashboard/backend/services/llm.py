"""OpenAI-compatible LLM client abstraction.

All vendor-specific details are isolated here. Switching providers only
requires changing three env vars: LLM_BASE_URL, LLM_API_KEY, LLM_MODEL.

BOB_API_KEY in .env maps to LLM_API_KEY via config.py.
"""
from __future__ import annotations

import logging

from openai import OpenAI

from config import settings

logger = logging.getLogger(__name__)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
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
