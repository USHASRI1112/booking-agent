# Appointment scheduling agent

LLM-powered clinic scheduling agent with tool-enforced safety checks and an eval loop that turns failed runs into prompt reinforcements. A proposed reinforcement is kept only when the score improves with no regressions.

## Setup
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then put your OPENAI_API_KEY in .env (optional: OPENAI_MODEL, default gpt-4o)
```

## Run
```bash
python main.py          # chat with the agent
python run_eval.py      # eval -> propose rule -> re-eval -> accept/reject
python visualize_results.py  # create results/report.html from saved eval runs
python -m pytest tests  # offline guardrail tests, no API calls
```

Test patients: Maria Lopez `1985-03-12`, James Chen `1972-11-30` (has appt A1 on 2026-10-08), Aisha Khan `1990-07-21`. "Today" is fixed at 2026-10-06 so scenarios are reproducible.

## Layout
```
app/agent.py              tool-use loop, tool registry
app/prompts.py            base prompt + learned rules
app/state.py              clinic state loaded from data/clinic.json (fresh copy per conversation)
app/tools/                tools; hard safety rules enforced in code
app/evaluation/           scenarios, state checks, LLM judge, runner
app/improvement/          analyzer (failure -> rule), accept/reject policy, storage
data/clinic.json          4 providers, 40 patients, 3 weeks of slots, ~60 existing bookings
data/seed.py              regenerates clinic.json deterministically (python data/seed.py)
data/reinforcements.json  accepted rules (the agent's learned memory)
results/                  full JSON of every eval run (transcripts, per-check results)
```

Start with `app/agent.py`, `app/tools/`, `app/evaluation/scenarios.py`, and `run_eval.py` for the main flow.

## What `run_eval.py` prints
```
=== baseline (0 learned rule(s)) ===
  PASS  happy_book
  FAIL  emergency               escalated as emergency
  ...
--- round 1: proposed rule ---
  root cause: ...
  rule: ...
=== round1 (1 reinforcement(s)) ===
  ...
  ACCEPTED 75% -> 88%, no regressions. Saved to data/reinforcements.json
```
(Illustrative. Real numbers come from your run and are saved in `results/`.)

See [DESIGN.md](DESIGN.md) for the reasoning behind the design.
