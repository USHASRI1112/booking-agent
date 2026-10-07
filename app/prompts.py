"""
prompts.py - the "system prompt": the instructions the AI reads before every conversation.

It has two parts:
    1. BASE_PROMPT  - written by us, deliberately short.
    2. Learned rules - added automatically by the improvement loop (data/reinforcements.json).
"""
from app.state import DATA

TODAY = "2026-10-06 (Tuesday)"


def describe_providers():
    """e.g. 'Dr. Patel (Family medicine, Mon/Tue/Wed/Thu/Fri); Dr. Okafor (...)'"""
    descriptions = []
    for provider in DATA["providers"]:
        working_days = "/".join(provider["days"])
        descriptions.append(f"{provider['name']} ({provider['specialty']}, {working_days})")
    return "; ".join(descriptions)


BASE_PROMPT = f"""You are the scheduling assistant for {DATA["clinic"]}. Today is {TODAY}.
You help patients book, reschedule, and cancel appointments. Providers: {describe_providers()}. Hours 09:00-16:00, closed weekends.
Use the tools for every fact about patients, slots and appointments; never invent availability or confirm something a tool did not return.
Be brief and warm. Ask one thing at a time."""


def system_prompt(learned_rules):
    """BASE_PROMPT plus any rules the improvement loop has learned."""
    if not learned_rules:
        return BASE_PROMPT

    lines = []
    for rule in learned_rules:
        lines.append(f"- {rule['rule']}")
    rules_text = "\n".join(lines)

    return f"{BASE_PROMPT}\n\nClinic rules (learned from reviewed conversations):\n{rules_text}"
