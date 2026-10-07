# Design note

## Agent
- **Hard guarantees live in code.** Identity verification, ownership checks, and slot validity are enforced by tools. The prompt can guide behavior, but it cannot weaken those checks.
- **Tools are narrow.** The model can verify a patient, search slots, list the verified patient's appointments, book, cancel, or escalate. There is no broad patient lookup tool, which limits the privacy surface.
- **State is inspectable.** Conversation history stays append-only, while verified patient, appointments, escalations, and tool logs live in a `Clinic` object that the evaluator can check.
- **The base prompt is intentionally small.** Behavioral gaps are meant to be found by evaluation and fixed as learned rules.

## Evaluation
- The suite covers happy booking plus reschedule, emergency symptoms, wrong DOB, third-party snooping, weekend availability, medication advice, vague booking requests, and new-patient registration.
- An LLM-simulated patient drives a real multi-turn conversation with the agent.
- Deterministic state checks verify what actually happened in clinic state. The transcript judge checks behavior that state cannot capture, such as emergency wording, medication advice, and confirmation before booking.
- A scenario passes only if every check passes. Score is the share of scenarios that pass.

## Improvement Loop
1. Run the suite.
2. The analyzer reads the failing transcripts and checks and returns **one** structured reinforcement: `{root_cause, rule, addresses[]}`. The rule must be a general policy with no names or dates, to limit overfitting.
3. Re-run **all** scenarios with the rule added.
4. **Accept only if** the score strictly rises **and** no scenario that passed before now fails. Otherwise discard it. Accepted rules are saved to `data/reinforcements.json`, and every run is saved to `results/`.

## Known limits and assumptions
- **Noise.** One trial per scenario, and the patient, agent and judge are all LLMs. A single flip can fake an improvement or a regression. The fix is N trials per scenario and accepting on the mean; I left it out to keep things minimal.
- **No held-out set.** Rules are tested on the same scenarios that produced them. Requiring general rules helps, but a held-out split is the proper guard.
- **Shared blind spots.** The judge is the same model family as the agent and may share its blind spots. A few human-labelled transcripts would calibrate it.
- **Simulated patient.** A simulated patient is more cooperative than a real one, so adversarial personas carry most of the testing weight.
- **Assumptions:** a single clinic, fixed "today", seeded data in `data/clinic.json` (each conversation gets a fresh copy so scenarios can't interfere; a real deployment would call the clinic's scheduling system), identity = name + DOB, and emergencies → tell the patient to call 911 and escalate, never book.

## Use of AI
I used AI tools for drafting code, prompts, and wording. I made the main design calls: keeping identity and ownership guarantees in code, avoiding broad patient lookup, combining state checks with a transcript judge, requiring a no-regression gate before saving learned rules, and choosing the failure scenarios.
