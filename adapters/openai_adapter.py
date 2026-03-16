"""
AgentRecall / adapters/openai_adapter.py
─────────────────────────────────────────
Reference adapter for the OpenAI Chat Completions API.
Copy this file and rename it to target any other agent or API.

The only contract this file must satisfy:
    def chat(message: str, history: list[dict], session_id: str | None) -> str

Requirements:
    pip install openai
    export OPENAI_API_KEY=sk-...
"""

import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

SYSTEM_PROMPT = """You are a helpful assistant. Pay close attention to everything
the user tells you and remember it accurately throughout the conversation."""

MODEL = "gpt-4o"   # swap to gpt-3.5-turbo, o3-mini, etc. for comparative runs


def chat(message: str, history: list[dict], session_id: str | None = None) -> str:
    """
    Send a message (with full history) to the model and return the reply.
    session_id is available if your agent supports persistent memory lookup —
    for standard OpenAI this is unused.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0,   # deterministic — important for reproducible scoring
    )
    return response.choices[0].message.content


# ────────────────────────────────────────────────────────────────────────────────
# Template: copy this block to create a new adapter
# ────────────────────────────────────────────────────────────────────────────────
#
# def chat(message: str, history: list[dict], session_id: str | None = None) -> str:
#     # 1. Build your payload from `history` + `message`
#     # 2. Call your agent / API
#     # 3. Return the agent's reply as a plain string
#     pass
