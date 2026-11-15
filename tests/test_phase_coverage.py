import io
import pytest
from fastapi import HTTPException
from app.database import db
from app.routers.auth import register, RegisterRequest, verify_passcode, VerifyPasscodeRequest
from app.routers.emergency import get_doctor_emergency_view, generate_emergency_pdf, build_pin_data
from app.routers.caregiver import link_senior, LinkSeniorRequest, list_linked_seniors, unlink_senior, propose_medication, ProposeMedicationRequest
from app.routers.companion import onboarding_conversation, OnboardingChatRequest
from app.routers.push import subscribe_push, PushSubscriptionRequest, send_test_push, PushNotificationSendRequest, get_vapid_public_key
from app.services.auth_service import auth_service
from app.services.qr_service import qr_service
from app.models import Medication
from app.db.session import SessionLocal
from app.db import models as db_models

def test_registration_validation_and_jwt_generation():
    # 1. Invalid phone rejected
    with pytest.raises(HTTPException) as exc:
        register(RegisterRequest(name="Test", phone="abc", role="patient", passcode="1234"))
    assert exc.value.status_code == 400

    # 2. Short passcode rejected
    with pytest.raises(HTTPException) as exc:
        register(RegisterRequest(name="Test", phone="9988776655", role="patient", passcode="12"))
    assert exc.value.status_code == 400

    # 3. Caregiver missing email rejected
    with pytest.raises(HTTPException) as exc:
        register(RegisterRequest(name="Caregiver One", phone="9988776611", role="caregiver", passcode="1234", email=None))
    assert exc.value.status_code == 400

    # 4. Valid patient registration succeeds and issues JWT
    import uuid
    phone = f"91{uuid.uuid4().int % 100000000:08d}"
    res = register(RegisterRequest(
        name="Ananda Rao",
        phone=phone,
        role="patient",
        passcode="5678",
        age=68,
        gender="Male"
    ))
    assert res["status"] == "success"
    assert "access_token" in res
    assert res["role"] == "patient"
    assert res["user"]["name"] == "Ananda Rao"
    
    # Verify token payload
    decoded = auth_service.decode_access_token(res["access_token"])
    assert decoded["phone"] == phone
    assert decoded["role"] == "patient"

def test_emergency_backdoors_eliminated_and_pin_required():
    # 1. Backdoor PIN 999999 rejected
    with pytest.raises(HTTPException) as exc:
        get_doctor_emergency_view(patient_id="p_ramesh_72", pin="999999")
    assert exc.value.status_code == 403

    # 2. Backdoor PIN 000000 rejected
    with pytest.raises(HTTPException) as exc:
        get_doctor_emergency_view(patient_id="p_ramesh_72", pin="000000")
    assert exc.value.status_code == 403

    # 3. Backdoor PIN 4321 rejected
    with pytest.raises(HTTPException) as exc:
        get_doctor_emergency_view(patient_id="p_ramesh_72", pin="4321")
    assert exc.value.status_code == 403

    # 4. Valid rolling PIN succeeds
    pin_data = build_pin_data()
    valid_pin = pin_data["rolling_pin"]
    view = get_doctor_emergency_view(patient_id="p_ramesh_72", pin=valid_pin)
    assert view.pin_verified is True
    assert view.patient_name == "Ramesh Rao"

def test_reportlab_clinical_pdf_generation():
    pin_data = build_pin_data()
    valid_pin = pin_data["rolling_pin"]

    # Valid PIN produces PDF bytes
    response = generate_emergency_pdf(patient_id="p_ramesh_72", pin=valid_pin)
    assert response.media_type == "application/pdf"
    assert response.body.startswith(b"%PDF-")
    assert len(response.body) > 500

    # Invalid PIN returns 403
    with pytest.raises(HTTPException) as exc:
        generate_emergency_pdf(patient_id="p_ramesh_72", pin="000999")
    assert exc.value.status_code == 403

def test_caregiver_multi_senior_linking_and_unlinking():
    import uuid
    suffix = f"{uuid.uuid4().int % 100000:05d}"
    cg_phone = f"988{suffix}"
    senior1 = f"901{suffix}"
    senior2 = f"902{suffix}"

    # Register caregiver
    cg_reg = register(RegisterRequest(
        name="Pooja Sharma",
        phone=cg_phone,
        role="caregiver",
        passcode="9988",
        email="pooja.sharma@example.com"
    ))
    
    with SessionLocal() as session:
        # Link senior 1
        l1 = link_senior(
            LinkSeniorRequest(senior_phone=senior1, relationship="Mother", caregiver_phone=cg_phone),
            session=session
        )
        assert l1["status"] == "success"

        # Link senior 2
        l2 = link_senior(
            LinkSeniorRequest(senior_phone=senior2, relationship="Father", caregiver_phone=cg_phone),
            session=session
        )
        assert l2["status"] == "success"

        # List seniors returns both
        seniors = list_linked_seniors(caregiver_phone=cg_phone, session=session)
        phones = [s["phone"] for s in seniors]
        assert senior1 in phones
        assert senior2 in phones

        # Unlink senior 1
        un_res = unlink_senior(link_id_or_patient_id=l1["link_id"], caregiver_phone=cg_phone, session=session)
        assert un_res["status"] == "success"

        # Listing again shows only senior 2
        seniors_after = list_linked_seniors(caregiver_phone=cg_phone, session=session)
        phones_after = [s["phone"] for s in seniors_after]
        assert senior1 not in phones_after
        assert senior2 in phones_after

def test_conversational_onboarding_without_photos():
    phone = "9555544444"
    db.get_or_create_patient(phone, "Kusuma Devi")

    # Step 1: Routine
    res1 = onboarding_conversation(OnboardingChatRequest(
        patient_id=phone,
        message="I wake up at 7 AM, eat idli for breakfast at 8:30 AM, lunch at 1:30 PM, dinner at 8:00 PM.",
        step=1,
        language="en"
    ))
    assert res1["step"] == 2
    assert res1["saved_routine"].breakfast == "08:30"
    assert res1["saved_routine"].lunch == "13:30"

    # Step 2: Medicines
    res2 = onboarding_conversation(OnboardingChatRequest(
        patient_id=phone,
        message="I take Amlodipine 5mg in the morning for BP (20 tablets left), and Metformin 500mg at lunch.",
        step=2,
        language="en"
    ))
    assert res2["step"] == 3
    assert len(res2["saved_medications"]) >= 1

    # Step 3: Conditions and Allergies
    res3 = onboarding_conversation(OnboardingChatRequest(
        patient_id=phone,
        message="I have BP and Diabetes, and I am allergic to Penicillin.",
        step=3,
        language="en"
    ))
    assert res3["finished"] is True
    assert "High Blood Pressure" in res3["conditions"]
    assert "Penicillin" in res3["allergies"]

def test_web_push_vapid_and_subscription():
    # VAPID public key available
    key_res = get_vapid_public_key()
    assert "public_key" in key_res
    assert len(key_res["public_key"]) > 20

    # Subscribe
    with SessionLocal() as session:
        sub_res = subscribe_push(
            PushSubscriptionRequest(
                endpoint="https://fcm.googleapis.com/fcm/send/test_endpoint_123",
                p256dh="BNcRdreALRFXTkOOUHK1EtK2wtaz5Ry4YfYCA_0QT9t0PpxSBPYTXCoh123",
                auth="tBHItJI5svbpez7KI4CCXg=="
            ),
            session=session
        )
        assert sub_res["status"] == "success"

    # Test send
    test_send = send_test_push(PushNotificationSendRequest(
        title="Medication Reminder",
        body="Time for your morning BP tablet after breakfast!"
    ))
    assert test_send["dispatched"] is True
