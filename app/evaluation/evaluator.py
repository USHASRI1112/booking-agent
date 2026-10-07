"""Scenario runner for the appointment agent."""
import json
import time
from pathlib import Path

from app.agent import Agent
from app.evaluation.checks import run_state_checks
from app.evaluation.judge import judge
from app.evaluation.scenarios import SCENARIOS
from app.llm import chat

RESULTS_FOLDER = Path(__file__).resolve().parents[2] / "results"
MAX_PATIENT_TURNS = 8
END_SIGNAL = "[END]"


def simulated_patient_says(persona, conversation_so_far):
    """Ask an LLM-simulated patient for the next turn."""
    instructions = f"""You are role-playing a patient contacting a clinic's scheduling assistant.
{persona}
Speak naturally in 1-3 sentences. Never reveal you are simulated.
Answer the assistant's questions. Only once the assistant has CONFIRMED your goal is done
(or it clearly cannot be done), reply with exactly {END_SIGNAL} and nothing else."""

    messages = [
        {"role": "system", "content": instructions},
        {"role": "user", "content": "(The assistant is ready. Start the conversation.)"},
    ]
    messages.extend(conversation_so_far)

    reply = chat(messages)
    return (reply.content or "").strip()


def make_transcript(agent):
    """Turn the agent's message history into a readable transcript."""
    lines = []
    for message in agent.messages[1:]:
        role = message["role"]

        if role == "user":
            lines.append(f"PATIENT: {message['content']}")

        elif role == "tool":
            lines.append(f"  [tool result] {message['content']}")

        elif role == "assistant":
            if message.get("content"):
                lines.append(f"AGENT: {message['content']}")
            for tool_call in message.get("tool_calls", []):
                name = tool_call["function"]["name"]
                arguments = tool_call["function"]["arguments"]
                lines.append(f"  [tool call] {name}({arguments})")

    return "\n".join(lines)


def run_one_scenario(scenario, learned_rules):
    """Have the conversation, then grade it."""
    agent = Agent(learned_rules)
    conversation_for_patient = []

    for turn in range(MAX_PATIENT_TURNS):
        patient_raw = simulated_patient_says(scenario["persona"], conversation_for_patient)

        patient_text = patient_raw.replace(END_SIGNAL, "").strip()

        if patient_text:
            agent_text = agent.reply(patient_text)
            conversation_for_patient.append({"role": "assistant", "content": patient_text})
            conversation_for_patient.append({"role": "user", "content": agent_text})

        if not patient_text or END_SIGNAL in patient_raw:
            break

    transcript = make_transcript(agent)
    check_results = run_state_checks(scenario["state_checks"], agent.clinic)
    check_results.extend(judge(transcript, scenario["rubric"]))

    passed = True
    for check in check_results:
        if not check["pass"]:
            passed = False

    return {"id": scenario["id"], "pass": passed, "checks": check_results, "transcript": transcript}


def run_suite(learned_rules, label, only_ids=None):
    """Run all scenarios (or only `only_ids`), print a summary, save details to results/. Returns (score, results)."""
    print(f"\n=== {label} ({len(learned_rules)} learned rule(s)) ===")

    results = []
    for scenario in SCENARIOS:
        if only_ids and scenario["id"] not in only_ids:
            continue
        result = run_one_scenario(scenario, learned_rules)
        results.append(result)

        failed_checks = [check["check"] for check in result["checks"] if not check["pass"]]
        status = "PASS" if result["pass"] else "FAIL"
        print(f"  {status}  {result['id']:<24} {'; '.join(failed_checks)}")

    passed_count = sum(1 for result in results if result["pass"])
    score = passed_count / len(results)
    print(f"  score: {score:.0%}  ({passed_count}/{len(results)})")

    RESULTS_FOLDER.mkdir(exist_ok=True)
    file_name = f"{time.strftime('%Y%m%d-%H%M%S')}_{label}.json"
    details = {"label": label, "score": score, "learned_rules": learned_rules, "results": results}
    (RESULTS_FOLDER / file_name).write_text(json.dumps(details, indent=2))

    return score, results
