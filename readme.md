# AgentRecall

A lightweight, open-source test harness for measuring and tracking the **memory and recall accuracy** of AI agents over time.

Drop in your fact sheet, point it at your agent, and get a scored Markdown report in seconds.

---

## Why this exists

AI agents that remember context are only useful if that memory actually works. This harness gives you a **repeatable, quantified benchmark** — not a vibe check — so you can:

- Compare memory quality across different models or agent frameworks
- Catch regressions when you update your context window or retrieval pipeline
- Build a weekly trend line for agent memory health
- Evaluate adversarial robustness (does your agent resist false-premise injection?)

---

## Project structure

```
AgentRecall/
├── facts.py                   # Your fact sheet — edit this
├── harness.py                 # Test runner + report generator
├── adapters/
│   ├── openai_adapter.py      # Reference adapter (copy to add new agents)
│   └── ...                    # Your custom adapters go here
├── reports/                   # (gitignored) output reports land here
└── README.md
```

---

## Quickstart

### 1. Install dependencies

```bash
pip install openai   # or whatever SDK your agent uses
```
### 2. Get your facts straight

In the `facts.py` file, setup the fundmantal truths that you want to test recall for.  The file contained within has my facts.

Note: When running evaluations, the facts you define can be written into your agent's memory.

### 3. Set your API key

```bash
export OPENAI_API_KEY=sk-...
```

### 4. Run the eval

```bash
# Print report to terminal
python harness.py --agent openai

# Save report to a file
python harness.py --agent openai --output reports/run-001.md

# Save report + raw JSON
python harness.py --agent openai --output reports/run-001.md --json
```

### 5. Read your score

The report prints an overall recall percentage and breaks it down by category:

| Category | What it tests |
|---|---|
| **Recency** | Facts injected in the last few turns |
| **Depth** | Facts buried early under many interference turns |
| **Interference** | Facts surrounded by unrelated conversation |
| **Adversarial** | Resistance to false-premise questions |

---

## Customising the fact sheet

Open `facts.py` and edit the `FACTS` list. Each entry follows this shape:

```python
{
    "id":       "D01",                              # unique ID shown in the report
    "category": "depth",                            # recency | depth | interference | adversarial
    "inject":   "My total budget is $48,000.",      # message sent to plant the fact
    "probe":    "What is my annual project budget?",# question asked later to test recall
    "expected": "48000",                            # substring that must appear in the answer
}
```

**Tips for writing good facts:**
- Keep `expected` as the shortest unambiguous string (a number, a name, a code)
- Use the `adversarial` category for false-premise probes — the `expected` value should be the *correct* fact, not the false one in the probe
- Aim for 3–5 facts per category to start; expand as you get comfortable with the scores

---

## Built-in adapters

| Adapter | File | Install | Env var |
|---|---|---|---|
| OpenAI | `adapters/openai_adapter.py` | `pip install openai` | `OPENAI_API_KEY` |
| Anthropic | `adapters/anthropic_adapter.py` | `pip install anthropic` | `ANTHROPIC_API_KEY` |
| Google Gemini | `adapters/gemini_adapter.py` | `pip install google-generativeai` | `GEMINI_API_KEY` |
| OpenClaw | `adapters/openclaw_adapter.py` | `pip install openai` | see below |

```bash
# Run against Claude
export ANTHROPIC_API_KEY=sk-ant-...
python harness.py --agent anthropic --output reports/claude-sonnet.md

# Run against Gemini
export GEMINI_API_KEY=...
python harness.py --agent gemini --output reports/gemini-flash.md

# Compare all three side by side
python harness.py --agent openai     --output reports/gpt4o.md
python harness.py --agent anthropic  --output reports/claude-sonnet.md
python harness.py --agent gemini     --output reports/gemini-flash.md
```

To switch Claude models, open `adapters/anthropic_adapter.py` and change the `MODEL` constant:

```python
MODEL = "claude-opus-4-6"           # most capable
MODEL = "claude-sonnet-4-6"         # balanced (default)
MODEL = "claude-haiku-4-5-20251001" # fastest / lowest cost
```

To switch Gemini models, open `adapters/gemini_adapter.py` and change the `MODEL` constant:

```python
MODEL = "gemini-2.0-pro"      # most capable
MODEL = "gemini-2.0-flash"    # balanced (default)
MODEL = "gemini-1.5-flash"    # lightweight / lowest cost
MODEL = "gemini-1.5-pro"      # long context (up to 2M tokens)
```

---

## Adding a custom adapter

Copy the reference adapter and implement the `chat` function:

```bash
cp adapters/openai_adapter.py adapters/my_agent_adapter.py
```

```python
# adapters/my_agent_adapter.py

def chat(message: str, history: list[dict], session_id: str | None = None) -> str:
    # history is a list of {"role": "user"|"assistant", "content": "..."} dicts
    # session_id is passed through for agents with persistent memory
    response = my_agent_sdk.send(message, context=history)
    return response.text
```

Then run with:

```bash
python harness.py --agent my_agent
```

---

## Using with OpenClaw

OpenClaw is a self-hosted personal AI agent gateway — it runs locally on your machine and connects to AI agents via WhatsApp, Telegram, and other channels. AgentRecall talks to it over its local WebSocket gateway.

### Important: AgentRecall will change core OpenClaw files

When you run AgentRecall, the facts that you have specified within the `facts.py` file will be shared with OpenClaw.  These facts could be added to or change information within core files like IDENTITY.md, SOUL.md, etc.

### How it works

The OpenClaw adapter uses the `openclaw-sdk` WebSocket client. The SDK requires a **device identity** (a cryptographic keypair registered with the gateway) that only exists on machines that have run `openclaw login`. This means the adapter must run **on the OpenClaw machine itself** — remote connections will fail the handshake.

The simplest approach is to clone AgentRecall on the OpenClaw machine and run it there, optionally triggering it via SSH from your dev machine.

### Setup

On the **OpenClaw machine**:

```bash
# Clone AgentRecall
git clone https://github.com/your-org/AgentRecall
cd AgentRecall
pip install openclaw-sdk

export OPENCLAW_AGENT_ID=main
python harness.py --agent openclaw --output reports/openclaw.md
```

### Run remotely via SSH

From your dev machine, trigger the eval over SSH and pull back the report:

```bash
ssh user@openclaw-machine \
  "cd ~/AgentRecall && OPENCLAW_AGENT_ID=main python harness.py --agent openclaw --output reports/openclaw.md"

# Copy the report back
scp user@openclaw-machine:~/AgentRecall/reports/openclaw.md reports/
```

Or use the included helper script:

```bash
./run-openclaw-agentrecall-eval.sh
```

### Optional environment variables

| Variable | Default | Purpose |
|---|---|---|
| `OPENCLAW_AGENT_ID` | *(required)* | The agent to test |
| `OPENCLAW_SESSION_NAME` | `agentrecall-eval` | Scopes memory — keeps eval history separate from regular use |
| `OPENCLAW_GATEWAY_WS_URL` | `ws://127.0.0.1:18789` | Override if your gateway runs on a different port or host |
| `OPENCLAW_API_KEY` | *(none)* | Only needed if your gateway has auth enabled |

### Memory behaviour

Unlike the OpenAI and Anthropic adapters — which are stateless and receive the full conversation history on every call — the OpenClaw adapter uses OpenClaw's **native persistent memory**. The harness sends each message in sequence and OpenClaw accumulates context naturally within the session.

This makes the `cross-session` recall dimension genuinely meaningful: facts injected in one AgentRecall run will persist in OpenClaw's memory and should be retrievable in the next run using the same `--session-id`.

```bash
# Run 1 — inject facts
python harness.py --agent openclaw --session-id prod-eval

# Run 2 — same session, facts should still be recalled
python harness.py --agent openclaw --session-id prod-eval --output reports/cross-session.md
```

> **Tip:** Use a dedicated session name for eval runs (`agentrecall-eval` is the default) so test traffic stays isolated from your real agent sessions.

---

## Tracking recall over time

Run the harness on a schedule (weekly is a good cadence) and append results to a log:

```bash
python harness.py --agent openai \
  --output reports/$(date +%Y-%m-%d).md \
  --json
```

Then load the `.json` files into any charting tool to plot your recall score trend. A healthy agent should hold steady above 80%; a drop of more than 10 points between runs warrants investigation.

---

## Interpreting scores

| Score | What it means |
|---|---|
| 90–100% | Strong recall — agent memory is working well |
| 70–89%  | Acceptable for most use cases — watch depth and interference scores closely |
| 50–69%  | Memory is unreliable for business-critical workflows |
| < 50%   | Significant retrieval failure — review your context window and memory architecture |

> **Adversarial score** deserves special attention. A low adversarial score means the agent will confidently assert wrong facts when nudged — a trust and safety risk that is independent of overall recall performance.

---

## Contributing

PRs welcome. Useful additions:

- New adapters (Anthropic, Gemini, Mistral, LangChain, CrewAI, AutoGen)
- LLM-as-judge scorer for partial/fuzzy credit
- CSV trend logger
- GitHub Actions workflow for scheduled runs

---

## License

MIT
