import pytest
from fastapi import HTTPException
from app.main import health_check
from app.routers.medications import get_medications, log_dose, get_adherence_summary, LogDoseRequest
from app.routers.emergency import build_pin_data, get_doctor_emergency_view
from app.routers.auth import verify_passcode, VerifyPasscodeRequest
from app.routers.routine import get_routine, parse_voice_routine
from app.models import RoutineVoiceParseRequest

def test_health_check_endpoint():
    res = health_check()
    assert res["status"] == "healthy"
    assert "VayoCare" in res["service"]

def test_get_medications_endpoint():
    meds = get_medications()
    assert len(meds) >= 4
    assert any(m.brand_name == "Telmikem 40" for m in meds)

def test_log_dose_endpoint():
    req = LogDoseRequest(
        medication_id="m_telmisartan",
        status="taken",
        notes="Morning dose confirmed via API"
    )
    res = log_dose(req)
    assert res.status == "taken"
    assert res.medication_name == "Telmikem 40"

def test_adherence_summary_endpoint():
    summary = get_adherence_summary()
    assert "adherence_rate_pct" in summary
    assert "total_scheduled" in summary
    assert summary["adherence_rate_pct"] >= 0

def test_emergency_current_pin_endpoint():
    pin_data = build_pin_data()
    assert "rolling_pin" in pin_data
    assert len(pin_data["rolling_pin"]) == 6
    assert pin_data["valid_for_seconds"] > 0

def test_doctor_view_with_valid_pin():
    pin_data = build_pin_data()
    pin = pin_data["rolling_pin"]
    
    doc_data = get_doctor_emergency_view(patient_id="p_ramesh_72", pin=pin)
    assert doc_data.patient_name == "Ramesh Rao"
    assert doc_data.pin_verified is True
    assert len(doc_data.active_medications_and_salts) > 0

def test_doctor_view_invalid_pin_raises_403():
    with pytest.raises(HTTPException) as exc:
        get_doctor_emergency_view(patient_id="p_ramesh_72", pin="000123")
    assert exc.value.status_code == 403

def test_verify_passcode_endpoint():
    res = verify_passcode(VerifyPasscodeRequest(passcode="4321"))
    assert res.authenticated is True
    assert res.role == "caregiver"

    with pytest.raises(HTTPException) as exc:
        verify_passcode(VerifyPasscodeRequest(passcode="9999"))
    assert exc.value.status_code == 401

def test_voice_routine_parse_endpoint():
    req = RoutineVoiceParseRequest(
        patient_id="p_ramesh_72",
        voice_transcript="ఉదయం 8 గంటలకు లేస్తాను, టిఫిన్ 9:30 కి, భోజనం 1:30 కి, రాత్రి 8:30 కి తింటాను.",
        language="te"
    )
    routine = parse_voice_routine(req)
    assert routine.breakfast in ["09:30", "09:00"]
    assert routine.dinner == "20:30"
