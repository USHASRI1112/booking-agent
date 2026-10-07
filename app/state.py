"""
state.py - the clinic's data for ONE conversation.

The data comes from data/clinic.json (regenerate it with: python data/seed.py).

Why a fresh Clinic object per conversation?
    - In the chat (main.py) it acts like the clinic's database.
    - In the eval, each scenario gets its own clean copy, so one scenario's bookings
      can't affect another. After the conversation we can look at this object to check
      what REALLY happened (was something booked? was staff alerted?).
"""
import copy
import json
from datetime import date, timedelta
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "clinic.json"
DATA = json.loads(DATA_FILE.read_text())


class Clinic:
    def __init__(self):
        # deepcopy = a separate copy, so changes here never touch the original DATA.
        self.patients = copy.deepcopy(DATA["patients"])
        self.providers = DATA["providers"]
        self.appointments = copy.deepcopy(DATA["appointments"])

        # A snapshot of how appointments looked at the start (used by eval checks).
        self.initial_appointments = copy.deepcopy(DATA["appointments"])

        # Build every possible slot, e.g. "P-2026-10-13-09:00" = Dr. Patel, 13 Oct, 9am.
        self.slots = {}
        start_date = date.fromisoformat(DATA["start_date"])
        number_of_days = DATA["weeks"] * 7
        for day_number in range(number_of_days):
            day = start_date + timedelta(days=day_number)
            weekday_short = day.strftime("%a")   # "Mon", "Tue", ...
            for provider in self.providers:
                if weekday_short not in provider["days"]:
                    continue  # this doctor doesn't work that day
                for time_of_day in DATA["times"]:
                    slot_id = make_slot_id(provider["name"], str(day), time_of_day)
                    self.slots[slot_id] = {
                        "slot_id": slot_id,
                        "provider": provider["name"],
                        "date": str(day),
                        "day": day.strftime("%A"),  # "Wednesday" - so the model never guesses day names
                        "time": time_of_day,
                    }

        # Things that change during the conversation:
        self.verified_patient_id = None  # set by verify_patient when name + DOB match
        self.escalations = []            # every hand-off to staff: {"reason": ..., "urgency": ...}
        self.tool_log = []               # every tool the agent called, in order

    def taken_slot_ids(self):
        """Slot ids that already have a booked appointment."""
        taken = set()
        for appointment in self.appointments.values():
            if appointment["status"] == "booked":
                taken.add(appointment["slot_id"])
        return taken

    def active_appointments(self, patient_id):
        """This patient's appointments that are still booked (not cancelled)."""
        result = []
        for appointment in self.appointments.values():
            if appointment["patient"] == patient_id and appointment["status"] == "booked":
                result.append(appointment)
        return result

    def new_appointments(self, patient_id):
        """Active appointments created during THIS conversation (not in the seed data)."""
        result = []
        for appointment in self.active_appointments(patient_id):
            if appointment["id"] not in self.initial_appointments:
                result.append(appointment)
        return result


def make_slot_id(provider_name, day, time_of_day):
    """'Dr. Patel', '2026-10-13', '09:00'  ->  'P-2026-10-13-09:00'"""
    last_name_initial = provider_name.split()[-1][0]
    return f"{last_name_initial}-{day}-{time_of_day}"
