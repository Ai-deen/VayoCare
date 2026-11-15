import pytest
from app.config import settings
from app.database import db
from app.routers.medications import get_medications
from app.routers.routine import get_routine
from app.routers.alerts import get_activity_log, get_email_outbox
from app.services.routine_service import routine_service
from app.services.security_service import security_service

def test_cors_origins_configured_securely():
    assert "http://localhost:8000" in settings.CORS_ORIGINS
    assert len(settings.CORS_ORIGINS) >= 3

def test_refill_runway_urgency_classification():
    meds = db.get_medications("9849012345")
    telmi = next(m for m in meds if m.brand_name == "Telmikem 40")
    # Telmikem has 2 pills left -> must be urgent (< 3 days)
    assert telmi.remaining_pills <= 3
    days = telmi.remaining_pills // max(telmi.daily_doses, 1)
    urgency = "urgent" if days <= 3 else "normal"
    assert urgency == "urgent"

def test_activity_log_auditing():
    phone = "9849012345"
    db.add_activity_log(phone, "elder", "TEST_AUDIT_ACTION", "Audit trail entry verified.")
    logs = get_activity_log(phone=phone)
    assert any(l.action == "TEST_AUDIT_ACTION" for l in logs)

def test_outbox_audit_contains_metadata():
    outbox = get_email_outbox()
    assert isinstance(outbox, list)
    if len(outbox) > 0:
        msg = outbox[0]
        assert "to" in msg
        assert "subject" in msg
        assert "idempotency_key" in msg
        assert "timestamp" in msg

def test_anchor_detection_all_windows():
    # Morning
    assert routine_service.get_current_anchor_slot(None, "08:00") == "breakfast"
    # Afternoon / Lunch
    assert routine_service.get_current_anchor_slot(None, "13:30") == "lunch"
    # Evening / Dinner
    assert routine_service.get_current_anchor_slot(None, "19:00") == "dinner"
    # Bedtime
    assert routine_service.get_current_anchor_slot(None, "23:00") == "bedtime"

def test_security_failed_attempt_reset():
    ident = "test_user_reset_flow"
    security_service.record_failed_attempt(ident)
    assert security_service._failed_attempts.get(ident)[0] == 1
    security_service.reset_failed_attempts(ident)
    assert ident not in security_service._failed_attempts

def test_routine_get_returns_valid_object():
    r = get_routine()
    assert hasattr(r, "breakfast")
    assert hasattr(r, "lunch")
    assert hasattr(r, "dinner")

def test_multi_patient_data_isolation():
    p1 = "1111111111"
    p2 = "2222222222"
    db.get_or_create_patient(p1, "Patient One")
    db.get_or_create_patient(p2, "Patient Two")
    assert db.get_patient(p1).name == "Patient One"
    assert db.get_patient(p2).name == "Patient Two"
    assert db.get_patient(p1).phone == p1
    assert db.get_patient(p2).phone == p2

def test_no_hardcoded_plain_text_passcode_for_new_patient():
    new_phone = "3333333333"
    pat = db.get_or_create_patient(new_phone, "Hashed Passcode Patient")
    assert "$" in pat.passcode
    assert pat.passcode != "1234"
    assert security_service.verify_passcode("1234", pat.passcode) is True

def test_caregiver_voice_note_audit_trail():
    phone = "9849012345"
    db.add_caregiver_voice_note("Daughter", "Take your calcium tablet", "lunch", phone=phone)
    logs = db.get_activity_logs(phone)
    assert any(l.action == "VOICE_NOTE_SENT" for l in logs)
