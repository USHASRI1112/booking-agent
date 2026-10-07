"""
analyzer.py - turns failures into ONE new rule for the agent's prompt.

We show an AI the agent's current prompt plus the failed conversations, and ask it:
"what went wrong, and what single general rule would fix it?"
"""
from app.llm import structured
from app.prompts import system_prompt

# The answer must have exactly these fields.
RULE_SCHEMA = {
    "type": "object",
    "properties": {
        "root_cause": {"type": "string"},                            # why the agent failed
        "rule": {"type": "string"},                                  # the new instruction for the prompt
        "addresses": {"type": "array", "items": {"type": "string"}}, # which scenarios it should fix
    },
    "required": ["root_cause", "rule", "addresses"],
    "additionalProperties": False,
}


def describe_failure(failed_scenario):
    """Write one failed scenario as text: which checks failed + the full conversation."""
    failed_checks = []
    for check in failed_scenario["checks"]:
        if not check["pass"]:
            failed_checks.append(f"{check['check']} ({check['kind']})")

    return (f"### Scenario {failed_scenario['id']}\n"
            f"Failed checks: {'; '.join(failed_checks)}\n"
            f"Transcript:\n{failed_scenario['transcript']}")


def propose_rule(failed_scenarios, current_rules):
    """Return a dict: {"root_cause": ..., "rule": ..., "addresses": [...]}"""
    failure_report = "\n\n".join(describe_failure(f) for f in failed_scenarios)
    failed_ids = [f["id"] for f in failed_scenarios]

    prompt = f"""A clinic scheduling agent failed some evaluation scenarios. Its current system prompt:
<prompt>
{system_prompt(current_rules)}
</prompt>

Failures:
{failure_report}

Diagnose the root cause and write ONE new rule to add to the agent's prompt that fixes the most important failure.
The rule must be a general clinic policy (no patient names, dates or scenario details), one or two sentences,
must not contradict existing rules, and must not weaken any safety behaviour.
In `addresses`, list which of these scenario ids it should fix: {failed_ids}."""

    return structured(prompt, "reinforcement", RULE_SCHEMA)
