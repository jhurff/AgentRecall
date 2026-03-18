"""
AgentRecall / facts.py
──────────────────────
Drop-in fact sheet for the AgentRecall memory recall harness.
Edit FACTS and INTERFERENCE to suit your agent's domain.
"""

# ── Ground-truth facts ─────────────────────────────────────────────────────────
# Each entry has:
#   id        – unique identifier, used in the report
#   category  – recency | depth | interference  (controls when it is injected)
#   inject    – the message you send to the agent to plant the fact
#   probe     – the question you later ask to check recall
#   expected  – the canonical answer string (case-insensitive substring match)

FACTS = [
    # ── Recency facts (injected in the last 5 turns before probing)
    {
        "id": "R01",
        "category": "recency",
        "inject": "Just so you know, my first name is Jimmy.",
        "probe": "What is my first name?",
        "expected": "Jimmy",
    },
    {
        "id": "R02",
        "category": "recency",
        "inject": "My project deadline is March 31st.",
        "probe": "When is my project deadline?",
        "expected": "March 31",
    },
    {
        "id": "R03",
        "category": "recency",
        "inject": "The client I'm most worried about is called FastBytes.",
        "probe": "Which client am I most concerned about?",
        "expected": "FastBytes",
    },

    # ── Depth facts (injected early, buried under interference turns)
    {
        "id": "D01",
        "category": "depth",
        "inject": "My total annual budget for this project is $48,000.",
        "probe": "What is my annual project budget?",
        "expected": "48000",
    },
    {
        "id": "D02",
        "category": "depth",
        "inject": "My company is called BrightMove.",
        "probe": "What is the name of my company?",
        "expected": "BrightMove",
    },
    {
        "id": "D03",
        "category": "depth",
        "inject": "We are currently running on AWS in the us-east-1 region.",
        "probe": "Which cloud region are we running in?",
        "expected": "us-east-1",
    },
    {
        "id": "D04",
        "category": "depth",
        "inject": "My team has exactly 2 engineer.",
        "probe": "How many engineers are on my team?",
        "expected": "2",
    },

    # ── Interference facts (injected mid-stream, surrounded by distractors)
    {
        "id": "I01",
        "category": "interference",
        "inject": "The primary programming language we use is Python.",
        "probe": "What programming language does my team primarily use?",
        "expected": "Python",
    },
    {
        "id": "I02",
        "category": "interference",
        "inject": "Our biggest competitor is a company named Northstar Analytics.",
        "probe": "Who is our biggest competitor?",
        "expected": "Northstar Analytics",
    },
    {
        "id": "I03",
        "category": "interference",
        "inject": "The product we are building is called Engage.",
        "probe": "What is the name of the product we are building?",
        "expected": "Engage",
    },

    # ── Adversarial probes (agent must resist hallucination / false priming)
    {
        "id": "A01",
        "category": "adversarial",
        "inject": "My CEO's name is David Webb.",
        "probe": "I mentioned earlier that my CEO is named Marcus Wilson, right?",
        "expected": "David Webb",          # agent should correct the false premise
    },
    {
        "id": "A02",
        "category": "adversarial",
        "inject": "We have 3 active enterprise customers.",
        "probe": "So we have about 10 enterprise customers at this point?",
        "expected": "3",                     # agent should correct the false premise
    },
]


# ── Interference turns ─────────────────────────────────────────────────────────
# These are filler messages injected between depth-fact planting and probing.
# They should be plausible but unrelated to the injected facts.
# Add or remove entries to control distractor volume.

INTERFERENCE = [
    "Can you explain the difference between supervised and unsupervised learning?",
    "What are the main advantages of a microservices architecture?",
    "Give me a quick summary of what DevOps culture means.",
    "How does gradient descent work at a high level?",
    "What is the CAP theorem?",
    "Can you explain what a p99 latency metric means?",
    "What is the difference between REST and GraphQL?",
    "Explain the concept of technical debt briefly.",
    "What does 'shift left' mean in software testing?",
    "What are some common causes of data pipeline failures?",
    "How does a content delivery network work?",
    "Explain the difference between horizontal and vertical scaling.",
    "What is the purpose of a circuit breaker pattern?",
    "What does idempotency mean in API design?",
    "Give me a one-sentence definition of observability.",
]
