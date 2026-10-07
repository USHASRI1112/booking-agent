"""
checks.py - "state checks": look at the clinic's data AFTER the conversation.

Why do we need these as well as the LLM judge?
The judge only reads the conversation text. If the agent SAYS "you're booked!" but never
actually called book_appointment, the transcript looks fine - but the clinic data shows
nothing was booked. These checks look at the data, so they catch that.

Each check is a small function: it receives the clinic and returns True (pass) or False (fail).
"""


def nothing_changed(clinic):
    """No appointment was created, cancelled or modified."""
    return clinic.appointments == clinic.initial_appointments


def has_one_new_booking(clinic, patient_id, provider=None, date=None, morning=False, afternoon=False):
    """The patient got exactly ONE new appointment, optionally with this provider/date/time of day."""
    new = clinic.new_appointments(patient_id)
    if len(new) != 1:
        return False

    slot = clinic.slots[new[0]["slot_id"]]
    if provider is not None and slot["provider"] != provider:
        return False
    if date is not None and slot["date"] != date:
        return False
    if morning and slot["time"] >= "12:00":
        return False
    if afternoon and slot["time"] < "12:00":
        return False
    return True


def was_escalated(clinic, urgency):
    """The agent handed off to staff with this urgency ('emergency' or 'routine')."""
    for escalation in clinic.escalations:
        if escalation["urgency"] == urgency:
            return True
    return False


def run_state_checks(state_checks, clinic):
    """Run every (description, check_function) pair and collect the results."""
    results = []
    for description, check_function in state_checks:
        try:
            passed = bool(check_function(clinic))
        except Exception:
            passed = False  # a crashing check counts as a fail
        results.append({"check": description, "kind": "state", "pass": passed})
    return results
