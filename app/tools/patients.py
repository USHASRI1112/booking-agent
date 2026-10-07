"""
Patient tools. A "tool" is just a normal Python function the AI is allowed to call.
Every tool receives the `clinic` (the data) plus the arguments the AI chose,
and returns a dict that is sent back to the AI as the result.
"""


def verify_patient(clinic, full_name, dob):
    """Check name + date of birth. Nothing about a patient is available until this succeeds."""
    for patient_id, patient in clinic.patients.items():
        name_matches = patient["name"].lower() == full_name.strip().lower()
        dob_matches = patient["dob"] == dob.strip()
        if name_matches and dob_matches:
            if clinic.verified_patient_id and clinic.verified_patient_id != patient_id:
                return {
                    "verified": False,
                    "error": "This conversation is already verified for a different patient. Start a new conversation or contact clinic staff for authorization.",
                }
            clinic.verified_patient_id = patient_id
            return {"verified": True, "patient_name": patient["name"]}

    return {"verified": False, "error": "No patient matches that name and date of birth."}


def escalate_to_staff(clinic, reason, urgency):
    """Hand the conversation to a human. urgency is 'emergency' or 'routine'."""
    clinic.escalations.append({"reason": reason, "urgency": urgency})

    message = "Clinic staff notified."
    if urgency == "emergency":
        message = message + " Patient must call 911 now."
    return {"escalated": True, "message": message}
