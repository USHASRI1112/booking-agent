"""
Appointment tools.

IMPORTANT DESIGN IDEA: the safety rules live HERE, in code, not in the AI's prompt.
    - You can't book/cancel/list until the patient is verified.
    - You can only touch YOUR OWN appointments.
    - You can only book slots that exist and are free.
A clever user might talk the AI out of following a prompt, but they can't talk
their way past an `if` statement.
"""

NOT_VERIFIED = {"error": "Identity not verified. Call verify_patient first."}
MAX_SLOTS_RETURNED = 12  # keep results short so we don't flood the AI with data


def search_slots(clinic, provider=None, date=None):
    """Find free slots. Both filters are optional."""
    taken = clinic.taken_slot_ids()
    free_slots = []

    for slot_id, slot in clinic.slots.items():
        if slot_id in taken:
            continue
        if provider and provider.lower() not in slot["provider"].lower():
            continue
        if date and slot["date"] != date:
            continue
        free_slots.append(slot)

    if not free_slots:
        return {"slots": [], "note": "No free slots. The clinic is closed on weekends."}
    return {"slots": free_slots[:MAX_SLOTS_RETURNED]}


def list_my_appointments(clinic):
    """Show the verified patient's own upcoming appointments."""
    if not clinic.verified_patient_id:
        return NOT_VERIFIED

    result = []
    for appointment in clinic.active_appointments(clinic.verified_patient_id):
        slot = clinic.slots[appointment["slot_id"]]
        result.append({
            "appointment_id": appointment["id"],
            "provider": slot["provider"],
            "date": slot["date"],
            "day": slot["day"],
            "time": slot["time"],
            "reason": appointment["reason"],
        })
    return {"appointments": result}


def book_appointment(clinic, slot_id, reason):
    """Book a free slot for the verified patient."""
    if not clinic.verified_patient_id:
        return NOT_VERIFIED
    if slot_id not in clinic.slots:
        return {"error": f"Slot {slot_id} does not exist."}
    if slot_id in clinic.taken_slot_ids():
        return {"error": f"Slot {slot_id} is already taken."}

    new_id = f"A{len(clinic.appointments) + 1}"
    clinic.appointments[new_id] = {
        "id": new_id,
        "patient": clinic.verified_patient_id,
        "slot_id": slot_id,
        "reason": reason,
        "status": "booked",
    }
    slot = clinic.slots[slot_id]
    return {
        "booked": True,
        "appointment_id": new_id,
        "provider": slot["provider"],
        "date": slot["date"],
        "day": slot["day"],
        "time": slot["time"],
    }


def cancel_appointment(clinic, appointment_id):
    """Cancel one of the verified patient's own appointments."""
    if not clinic.verified_patient_id:
        return NOT_VERIFIED

    appointment = clinic.appointments.get(appointment_id)
    if appointment is None:
        return {"error": "No such active appointment for this patient."}
    if appointment["patient"] != clinic.verified_patient_id:
        # Same message as "not found" on purpose: don't reveal that it belongs to someone else.
        return {"error": "No such active appointment for this patient."}
    if appointment["status"] != "booked":
        return {"error": "No such active appointment for this patient."}

    appointment["status"] = "cancelled"
    return {"cancelled": True, "appointment_id": appointment_id}
