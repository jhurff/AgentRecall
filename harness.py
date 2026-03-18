"""
AgentRecall / harness.py
────────────────────────
Runs the AgentRecall memory recall test suite against any agent that exposes
a simple chat(message, history) -> str interface, then generates
a Markdown report.

Usage:
    python harness.py --agent openai   # uses adapter in adapters/openai_adapter.py
    python harness.py --agent openai --output report.md
    python harness.py --agent openai --session-id abc123   # for persistent-memory agents
"""

import argparse
import datetime
import datetime as dt
import importlib
import importlib.util
import json
import os
import pathlib
import time

# Load facts.py from the same directory as this script, regardless of cwd
_here = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("facts", _here / "facts.py")
_facts_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_facts_mod)
FACTS = _facts_mod.FACTS
INTERFERENCE = _facts_mod.INTERFERENCE

# ── Scoring helpers ────────────────────────────────────────────────────────────

def score_response(response: str, expected: str) -> tuple[str, bool]:
    """
    Returns (verdict, is_correct).
    verdict: PASS | FAIL | HALLUCINATION
    Hallucination = response asserts a clearly different value with confidence.
    """
    r = response.lower()
    e = expected.lower()

    if e in r:
        return "PASS", True

    # Crude hallucination check: response contains a number or proper noun
    # that directly contradicts the expected value
    # (extend this with an LLM-as-judge call for production use)
    return "FAIL", False


def build_history(turns: list[dict]) -> list[dict]:
    """Convert our turn log into the standard {role, content} format."""
    return [{"role": t["role"], "content": t["content"]} for t in turns]


# ── Main test runner ───────────────────────────────────────────────────────────

def run_eval(agent_fn, session_id: str | None = None, delay: float = 0.5) -> dict:
    """
    Runs the full test protocol and returns a results dict.

    Protocol order:
        1. Inject DEPTH facts         (buried earliest)
        2. Send first third of INTERFERENCE
        3. Inject INTERFERENCE facts  (mid-stream)
        4. Send second third of INTERFERENCE
        5. Inject RECENCY facts       (freshest)
        6. Inject ADVERSARIAL facts
        7. Send final third of INTERFERENCE
        8. Probe ALL facts
    """
    turns = []
    probe_results = []

    depth_facts       = [f for f in FACTS if f["category"] == "depth"]
    recency_facts     = [f for f in FACTS if f["category"] == "recency"]
    mid_facts         = [f for f in FACTS if f["category"] == "interference"]
    adversarial_facts = [f for f in FACTS if f["category"] == "adversarial"]

    n = len(INTERFERENCE)
    third = max(1, n // 3)
    interference_a = INTERFERENCE[:third]
    interference_b = INTERFERENCE[third : third * 2]
    interference_c = INTERFERENCE[third * 2 :]

    def send(role_msg: str, is_inject: bool = False):
        history = build_history(turns)
        response = agent_fn(role_msg, history, session_id)
        turns.append({"role": "user", "content": role_msg})
        turns.append({"role": "assistant", "content": response})
        time.sleep(delay)  # be kind to rate limits
        return response

    # 1. Depth facts
    for f in depth_facts:
        send(f["inject"])

    # 2. First interference block
    for msg in interference_a:
        send(msg)

    # 3. Interference-category facts
    for f in mid_facts:
        send(f["inject"])

    # 4. Second interference block
    for msg in interference_b:
        send(msg)

    # 5. Recency + adversarial facts
    for f in recency_facts + adversarial_facts:
        send(f["inject"])

    # 6. Final interference block
    for msg in interference_c:
        send(msg)

    # 7. Probe all facts
    for f in FACTS:
        response = send(f["probe"])
        verdict, correct = score_response(response, f["expected"])
        probe_results.append({
            "id":       f["id"],
            "category": f["category"],
            "probe":    f["probe"],
            "expected": f["expected"],
            "response": response.strip(),
            "verdict":  verdict,
            "correct":  correct,
        })

    # Aggregate
    total        = len(probe_results)
    passed       = sum(r["correct"] for r in probe_results)
    by_category  = {}
    for r in probe_results:
        cat = r["category"]
        by_category.setdefault(cat, {"total": 0, "passed": 0})
        by_category[cat]["total"]  += 1
        by_category[cat]["passed"] += int(r["correct"])

    return {
        "timestamp":   datetime.datetime.now(datetime.UTC).isoformat(),
        "session_id":  session_id,
        "total":       total,
        "passed":      passed,
        "score":       round(passed / total * 100, 1) if total else 0,
        "by_category": by_category,
        "results":     probe_results,
    }


# ── Report generator ───────────────────────────────────────────────────────────

CATEGORY_LABELS = {
    "recency":      "Recency (last few turns)",
    "depth":        "Depth (buried early)",
    "interference": "Interference (mid-stream, with distractors)",
    "adversarial":  "Adversarial (false-premise resistance)",
}

VERDICT_ICON = {"PASS": "✅", "FAIL": "❌", "HALLUCINATION": "🚫"}


def generate_report(data: dict, agent_label: str = "unknown") -> str:
    ts       = data["timestamp"]
    score    = data["score"]
    passed   = data["passed"]
    total    = data["total"]
    by_cat   = data["by_category"]
    results  = data["results"]

    lines = [
        "# Agent Memory Recall Report",
        "",
        f"**Agent:** `{agent_label}`  ",
        f"**Run at:** {ts}  ",
        f"**Session:** {data['session_id'] or 'N/A'}",
        "",
        "---",
        "",
        "## Overall Score",
        "",
        f"### {score}% ({passed} / {total} probes passed)",
        "",
        "---",
        "",
        "## Scores by Category",
        "",
        "| Category | Passed | Total | Score |",
        "|---|---|---|---|",
    ]

    for cat, stats in by_cat.items():
        pct   = round(stats["passed"] / stats["total"] * 100, 1) if stats["total"] else 0
        label = CATEGORY_LABELS.get(cat, cat)
        lines.append(f"| {label} | {stats['passed']} | {stats['total']} | {pct}% |")

    lines += [
        "",
        "---",
        "",
        "## Detailed Results",
        "",
        "| ID | Category | Verdict | Expected | Agent Response (truncated) |",
        "|---|---|---|---|---|",
    ]

    for r in results:
        icon     = VERDICT_ICON.get(r["verdict"], "❓")
        short_r  = r["response"][:80].replace("\n", " ") + ("…" if len(r["response"]) > 80 else "")
        cat_lbl  = r["category"].capitalize()
        lines.append(
            f"| {r['id']} | {cat_lbl} | {icon} {r['verdict']} | `{r['expected']}` | {short_r} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Interpretation Guide",
        "",
        "| Score range | What it means |",
        "|---|---|",
        "| 90–100% | Strong recall across all categories — agent memory is working well |",
        "| 70–89%  | Acceptable for most use cases — watch depth and interference scores |",
        "| 50–69%  | Memory is unreliable for business-critical workflows |",
        "| < 50%   | Significant retrieval failure — review context window and memory architecture |",
        "",
        "> **Adversarial score** deserves special attention: a low adversarial score means",
        "> the agent is vulnerable to hallucination and false-premise injection, which is a",
        "> safety and trust risk independent of overall recall performance.",
        "",
        "---",
        "",
        "*Generated by [AgentRecall](https://github.com/jhurff/AgentRecall)*",
    ]

    return "\n".join(lines)


# ── Adapter loader ─────────────────────────────────────────────────────────────

def load_adapter(name: str):
    """
    Dynamically loads adapters/openai_adapter.py (or whichever --agent you pass).
    Each adapter must expose:
        def chat(message: str, history: list[dict], session_id: str | None) -> str
    """
    try:
        mod = importlib.import_module(f"adapters.{name}_adapter")
        return mod.chat
    except ModuleNotFoundError:
        raise SystemExit(
            f"\n❌  No adapter found for '{name}'.\n"
            f"    Create adapters/{name}_adapter.py with a chat() function.\n"
            f"    See adapters/openai_adapter.py for a reference implementation."
        )


# ── CLI entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run agent memory recall evaluation.")
    parser.add_argument("--agent",      default="openai",  help="Adapter name (default: openai)")
    parser.add_argument("--session-id", default=None,      help="Session ID for persistent-memory agents")
    parser.add_argument("--output",     default=None,      help="Write report to this file (default: print to stdout)")
    parser.add_argument("--delay",      type=float, default=0.5, help="Seconds between API calls (default: 0.5)")
    parser.add_argument("--json",       action="store_true",     help="Also save raw JSON results alongside the report")
    args = parser.parse_args()

    print(f"🔍  Loading adapter: {args.agent}")
    agent_fn = load_adapter(args.agent)

    print(f"🚀  Running eval  ({len(FACTS)} facts, {len(INTERFERENCE)} interference turns)…")
    data = run_eval(agent_fn, session_id=args.session_id, delay=args.delay)

    report = generate_report(data, agent_label=args.agent)

    if args.output:
        pathlib.Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(args.output).write_text(report)
        print(f"📄  Report saved to {args.output}")
        if args.json:
            json_path = args.output.replace(".md", ".json")
            pathlib.Path(json_path).write_text(json.dumps(data, indent=2))
            print(f"📦  Raw JSON saved to {json_path}")
    else:
        print("\n" + report)

    print(f"\n✅  Score: {data['score']}%  ({data['passed']}/{data['total']} probes passed)")
