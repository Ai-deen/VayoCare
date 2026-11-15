import pytest
import time
from fastapi import HTTPException
from app.services.security_service import security_service
from app.routers.auth import verify_passcode, VerifyPasscodeRequest, phone_login
from app.models import PhoneAuthRequest
from app.database import db

def test_pbkdf2_passcode_hashing():
    pwd = "secret_pass_123"
    hashed = security_service.hash_passcode(pwd)
    assert "$" in hashed
    assert security_service.verify_passcode(pwd, hashed) is True
    assert security_service.verify_passcode("wrong_pass", hashed) is False

def test_passcode_verification_success():
    req = VerifyPasscodeRequest(passcode="4321", phone="9849012345")
    res = verify_passcode(req)
    assert res.authenticated is True
    assert res.role == "caregiver"

def test_magic_0000_passcode_backdoor_rejected():
    """Verify that insecure 0000 backdoor has been removed."""
    req = VerifyPasscodeRequest(passcode="0000", phone="9849012345")
    with pytest.raises(HTTPException) as exc:
        verify_passcode(req)
    assert exc.value.status_code == 401

def test_lockout_after_five_failed_attempts():
    phone = "9998887776"
    db.get_or_create_patient(phone, "Lockout Test Patient")
    security_service.reset_failed_attempts(phone)

    # 4 failed attempts: each returns 401
    for i in range(4):
        with pytest.raises(HTTPException) as exc:
            verify_passcode(VerifyPasscodeRequest(passcode="wrong", phone=phone))
        assert exc.value.status_code == 401

    # 5th failed attempt: triggers 429 lockout!
    with pytest.raises(HTTPException) as exc:
        verify_passcode(VerifyPasscodeRequest(passcode="wrong", phone=phone))
    assert exc.value.status_code == 429
    assert "lockout" in exc.value.detail.lower()

    # Subsequent attempt is locked out immediately
    with pytest.raises(HTTPException) as exc:
        verify_passcode(VerifyPasscodeRequest(passcode="1234", phone=phone))
    assert exc.value.status_code == 429

    # Reset
    security_service.reset_failed_attempts(phone)
    assert security_service.is_locked_out(phone)[0] is False

def test_phone_login_creates_isolated_patient():
    req = PhoneAuthRequest(role="patient", name="Sita Devi", phone="9112233445", language="hi")
    res = phone_login(req)
    assert res["status"] == "success"
    assert res["phone"] == "9112233445"
    assert res["patient"].name == "Sita Devi"
    assert res["patient"].language_preference == "hi"

def test_caregiver_links_to_patient():
    req = PhoneAuthRequest(
        role="caregiver",
        name="Vikram",
        phone="9876543210",
        patient_phone="9112233445"
    )
    res = phone_login(req)
    assert res["status"] == "success"
    assert res["linked_patient_phone"] == "9112233445"
    assert res["patient"].name == "Sita Devi"

def test_sql_injection_and_dirty_inputs_safely_sanitized():
    dirty_phone = "'; DROP TABLE patients; -- 9849012345"
    clean = db._normalize_phone(dirty_phone)
    assert clean == "9849012345"
    assert ";" not in clean
