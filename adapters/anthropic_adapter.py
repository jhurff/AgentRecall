"""
AgentRecall / adapters/anthropic_adapter.py
────────────────────────────────────────────
Adapter for the Anthropic Claude API (Messages endpoint).
Supports all Claude models including claude-opus-4-6, claude-sonnet-4-6,
and claude-haiku-4-5-20251001.

Requirements:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...
"""

import os
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """You are a helpful assistant. Pay close attention to everything
the user tells you and remember it accurately throughout the conversation."""

MODEL = "claude-sonnet-4-6"   # swap to claude-opus-4-6 or claude-haiku-4-5-20251001
MAX_TOKENS = 1024


def chat(message: str, history: list[dict], session_id: str | None = None) -> str:
    """
    Send a message (with full history) to Claude and return the reply.
    session_id is available if your agent uses persistent memory — unused here
    for the standard stateless Claude API.

    The Anthropic Messages API requires that the first message is from 'user'
    and that roles strictly alternate user/assistant. The harness guarantees
    this — history is always injected as alternating pairs.
    """
    messages = list(history)
    messages.append({"role": "user", "content": message})

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    return response.content[0].text
