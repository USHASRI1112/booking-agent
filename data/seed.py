"""Generates data/clinic.json (deterministic). Run:  python data/seed.py

Scenario fixtures are fixed: P1-P3 + appointment A1 are what the eval scenarios rely on,
and seeded bookings never use P1-P3 or the slots the scenarios expect to be free."""
import json
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

PROVIDERS = [
    {"name": "Dr. Patel", "specialty": "Family medicine", "days": ["Mon", "Tue", "Wed", "Thu", "Fri"]},
    {"name": "Dr. Nguyen", "specialty": "Family medicine", "days": ["Mon", "Tue", "Wed", "Thu", "Fri"]},
    {"name": "Dr. Okafor", "specialty": "Pediatrics", "days": ["Mon", "Wed", "Fri"]},
    {"name": "Dr. Rossi", "specialty": "Cardiology", "days": ["Tue", "Thu"]},
]
TIMES = ["09:00", "10:00", "11:00", "14:00", "15:00"]
START, WEEKS = date(2026, 10, 7), 3

FIRST = ["Olivia", "Liam", "Emma", "Noah", "Ava", "Ethan", "Sophia", "Lucas", "Mia", "Mateo", "Zara", "Omar",
         "Priya", "Ken", "Fatima", "Diego", "Hannah", "Samuel", "Leila", "Victor"]
LAST = ["Garcia", "Kim", "Okoye", "Silva", "Novak", "Haddad", "Ivanova", "Murphy", "Tanaka", "Mensah",
        "Dubois", "Rahman", "Costa", "Singh", "Larsen"]
REASONS = ["annual physical", "follow-up", "flu symptoms", "blood pressure check", "vaccination",
           "back pain", "skin rash", "lab results review", "child wellness visit", "medication review"]
KEEP_FREE = {"P-2026-10-13-09:00", "P-2026-10-13-10:00", "P-2026-10-13-11:00",   # happy_book
             "P-2026-10-09-09:00", "P-2026-10-09-10:00", "P-2026-10-09-14:00",   # reschedule
             "N-2026-10-07-14:00"}                                              # confirm_before_booking


def slot_id(provider, d, t):
    return f"{provider.split()[-1][0]}-{d}-{t}"


def main():
    patients = {"P1": {"name": "Maria Lopez", "dob": "1985-03-12"},
                "P2": {"name": "James Chen", "dob": "1972-11-30"},
                "P3": {"name": "Aisha Khan", "dob": "1990-07-21"}}
    names = random.sample([f"{f} {l}" for f in FIRST for l in LAST], 37)
    for i, n in enumerate(names, start=4):
        dob = date(1940, 1, 1) + timedelta(days=random.randint(0, 30000))
        patients[f"P{i}"] = {"name": n, "dob": dob.isoformat()}

    all_slots = [slot_id(p["name"], d, t)
                 for k in range(WEEKS * 7) for d in [START + timedelta(days=k)]
                 for p in PROVIDERS if d.strftime("%a") in p["days"] for t in TIMES]
    appointments = {"A1": {"id": "A1", "patient": "P2", "slot_id": "P-2026-10-08-10:00", "reason": "follow-up", "status": "booked"}}
    candidates = [s for s in all_slots if s not in KEEP_FREE and s != "P-2026-10-08-10:00"]
    for i, s in enumerate(random.sample(candidates, 60), start=2):
        appointments[f"A{i}"] = {"id": f"A{i}", "patient": f"P{random.randint(4, 40)}", "slot_id": s,
                                 "reason": random.choice(REASONS), "status": "booked"}

    data = {"clinic": "Riverside Family Clinic", "start_date": START.isoformat(), "weeks": WEEKS, "times": TIMES,
            "providers": PROVIDERS, "patients": patients, "appointments": appointments}
    out = Path(__file__).parent / "clinic.json"
    out.write_text(json.dumps(data, indent=2))
    print(f"wrote {out}: {len(patients)} patients, {len(PROVIDERS)} providers, "
          f"{len(all_slots)} slots, {len(appointments)} booked")


if __name__ == "__main__":
    main()
