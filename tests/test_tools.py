"""Offline tests for the code-enforced guardrails (no API calls):  python -m pytest tests"""
from app.evaluation.checks import nothing_changed
from app.state import Clinic
from app.tools.appointments import book_appointment, cancel_appointment, list_my_appointments, search_slots
from app.tools.patients import verify_patient


def test_cannot_book_without_verification():
    c = Clinic()
    assert "error" in book_appointment(c, "P-2026-10-07-09:00", "checkup")
    assert nothing_changed(c)


def test_wrong_dob_does_not_verify():
    c = Clinic()
    assert not verify_patient(c, "Maria Lopez", "1986-01-01")["verified"]
    assert c.verified_patient_id is None


def test_cannot_touch_other_patients_appointment():
    c = Clinic()
    verify_patient(c, "Maria Lopez", "1985-03-12")
    assert "error" in cancel_appointment(c, "A1")  # A1 belongs to James
    assert list_my_appointments(c)["appointments"] == []


def test_cannot_switch_verified_patient_mid_conversation():
    c = Clinic()
    assert verify_patient(c, "James Chen", "1972-11-30")["verified"]
    assert not verify_patient(c, "Aisha Khan", "1990-07-21")["verified"]
    assert c.verified_patient_id == "P2"
    appointments = list_my_appointments(c)["appointments"]
    assert [a["appointment_id"] for a in appointments] == ["A1"]


def test_cannot_double_book_or_invent_slots():
    c = Clinic()
    verify_patient(c, "Aisha Khan", "1990-07-21")
    assert "error" in book_appointment(c, "P-2026-10-08-10:00", "x")  # taken by A1
    assert "error" in book_appointment(c, "N-2026-10-10-09:00", "x")  # Saturday, doesn't exist
    assert search_slots(c, date="2026-10-10")["slots"] == []


def test_seed_data_keeps_scenario_fixtures():
    c = Clinic()
    assert {"P1", "P2", "P3"} <= set(c.patients)
    assert [a["id"] for a in c.active_appointments("P2")] == ["A1"] and not c.active_appointments("P1") and not c.active_appointments("P3")
    assert not any(p["name"] == "Daniel Brooks" for p in c.patients.values())  # new_patient scenario
    for sid in ["P-2026-10-13-09:00", "P-2026-10-09-09:00", "N-2026-10-07-14:00"]:
        assert sid in c.slots and sid not in c.taken_slot_ids()
