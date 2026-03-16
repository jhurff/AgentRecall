#pip install openclaw-sdk
export OPENCLAW_GATEWAY_WS_URL=ws://127.0.0.1:18789
#export OPENCLAW_GATEWAY_TOKEN=agentrecall-token
export OPENCLAW_AGENT_ID=main
python harness.py --agent openclaw --output reports/openclaw.md
