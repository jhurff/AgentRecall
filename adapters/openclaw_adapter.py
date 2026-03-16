"""
AgentRecall / adapters/openclaw_adapter.py
───────────────────────────────────────────
Adapter for OpenClaw — the self-hosted personal AI agent gateway.
https://github.com/openclaw/openclaw

IMPORTANT: This adapter must run ON the OpenClaw machine (or a machine
that has completed openclaw login). The OpenClaw SDK requires a local
device identity (Ed25519 keypair) that is registered with the gateway.
Running it remotely will fail with "invalid handshake".

The simplest approach is to clone AgentRecall on the OpenClaw machine
and run harness.py there directly (via SSH if needed).

Requirements:
    pip install openclaw-sdk

Environment variables:
    OPENCLAW_AGENT_ID      Agent ID to test (default: "main")
    OPENCLAW_SESSION_NAME  Session name for memory scoping (default: agentrecall-eval)
    OPENCLAW_GATEWAY_WS_URL  Override gateway URL (default: ws://127.0.0.1:18789)
    OPENCLAW_GATEWAY_TOKEN   Gateway auth token if required
"""

import asyncio
import os

from openclaw_sdk import OpenClawClient

AGENT_ID     = os.environ.get("OPENCLAW_AGENT_ID", "main")
SESSION_NAME = os.environ.get("OPENCLAW_SESSION_NAME", "agentrecall-eval")


def _build_client_config() -> dict:
    kwargs = {}
    if os.environ.get("OPENCLAW_GATEWAY_WS_URL"):
        kwargs["gateway_ws_url"] = os.environ["OPENCLAW_GATEWAY_WS_URL"]
    if os.environ.get("OPENCLAW_GATEWAY_TOKEN"):
        kwargs["api_key"] = os.environ["OPENCLAW_GATEWAY_TOKEN"]
    return kwargs


async def _chat_async(message: str, session_name: str) -> str:
    config_kwargs = _build_client_config()
    client = await OpenClawClient.connect(**config_kwargs)
    try:
        agent = client.get_agent(AGENT_ID, session_name=session_name)
        result = await agent.execute(message)
        return result.content
    finally:
        await client.close()


def chat(message: str, history: list[dict], session_id: str | None = None) -> str:
    """
    Send a message to the OpenClaw agent and return the reply.

    NOTE: history is intentionally not forwarded — OpenClaw manages its own
    persistent conversation history per session. Messages are sent in sequence
    and the agent accumulates context naturally within the session.
    """
    session_name = session_id or SESSION_NAME
    return asyncio.run(_chat_async(message, session_name))
