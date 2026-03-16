"""
AgentRecall / adapters/gemini_adapter.py
─────────────────────────────────────────
Adapter for the Google Gemini API (google-generativeai SDK).
Supports Gemini 2.0 and 1.5 model families.

Requirements:
    pip install google-generativeai
    export GEMINI_API_KEY=...   # get yours at https://aistudio.google.com/app/apikey
"""

import os
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

SYSTEM_PROMPT = """You are a helpful assistant. Pay close attention to everything
the user tells you and remember it accurately throughout the conversation."""

MODEL = "gemini-2.0-flash"   # swap to gemini-2.0-pro, gemini-1.5-flash, gemini-1.5-pro

# Generation config — temperature=0 for deterministic, reproducible scoring
GENERATION_CONFIG = genai.GenerationConfig(
    temperature=0,
    max_output_tokens=1024,
)

model = genai.GenerativeModel(
    model_name=MODEL,
    system_instruction=SYSTEM_PROMPT,
    generation_config=GENERATION_CONFIG,
)


def _to_gemini_history(history: list[dict]) -> list[dict]:
    """
    Convert standard {role, content} history to Gemini's {role, parts} format.
    Gemini uses 'model' instead of 'assistant' for the assistant role.
    """
    role_map = {"user": "user", "assistant": "model"}
    return [
        {"role": role_map[turn["role"]], "parts": [turn["content"]]}
        for turn in history
    ]


def chat(message: str, history: list[dict], session_id: str | None = None) -> str:
    """
    Send a message (with full history) to Gemini and return the reply.
    session_id is available if your agent uses persistent memory — unused here
    for the standard stateless Gemini API.

    Gemini's send_message() method manages the chat session internally,
    so we reconstruct the session from history on each call.
    """
    gemini_history = _to_gemini_history(history)
    chat_session = model.start_chat(history=gemini_history)
    response = chat_session.send_message(message)
    return response.text
