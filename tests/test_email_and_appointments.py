import pytest
from app.services.email_service import email_engine
from app.routers.appointments import create_appointment, list_appointments, cancel_appointment, download_ics_calendar, CreateAppointmentRequest
from app.routers.medications import create_medication, approve_medication, reject_medication, get_adherence_insights, CreateMedicationRequest
from app.database import db

def test_email_engine_sends_and_records_in_outbox():
    res = email_engine.send_email(
        to_email="son@example.com",
        subject="Test Medication Reminder",
        body_html="<p>Please take your BP tablet</p>",
        category="dose_reminder",
        idempotency_key="unique_key_001"
    )
    assert res["status"] == "success"
    assert res["to"] == "son@example.com"
    
    outbox = email_engine.get_outbox()
    assert any(m["idempotency_key"] == "unique_key_001" for m in outbox)

def test_email_idempotency_suppresses_duplicates():
    # Send same email with identical idempotency key
    res = email_engine.send_email(
        to_email="son@example.com",
        subject="Duplicate Check",
        body_html="<p>Duplicate</p>",
        idempotency_key="unique_key_001"  # Already sent above
    )
    assert res["status"] == "duplicate_suppressed"

def test_appointment_crud_and_calendar_export():
    phone = "9849012345"
    req = CreateAppointmentRequest(
        doctor_name="Dr. Ananya Sharma",
        specialty="Endocrinologist",
        hospital="Apollo Clinics",
        date="2026-12-05",
        time="11:00",
        notes="Diabetic 6-month HbA1c review",
        patient_phone=phone
    )
    appt = create_appointment(req)
    assert appt.doctor_name == "Dr. Ananya Sharma"
    assert appt.status == "scheduled"

    # List appointments
    appts = list_appointments(phone=phone)
    assert any(a.id == appt.id for a in appts)

    # Export .ics calendar
    ics_resp = download_ics_calendar(appt.id, phone=phone)
    assert ics_resp.status_code == 200
    assert "text/calendar" in ics_resp.media_type
    content = ics_resp.body.decode()
    assert "BEGIN:VCALENDAR" in content
    assert "Dr. Ananya Sharma" in content
    assert "END:VCALENDAR" in content

    # Cancel appointment
    cancel_res = cancel_appointment(appt.id, phone=phone)
    assert cancel_res["status"] == "success"

def test_caretaker_medication_proposal_requires_elder_consent():
    phone = "9849012345"
    # Caretaker adds medicine
    req = CreateMedicationRequest(
        name="Vitamin D3 Sachet",
        timing_anchor="lunch",
        dosage="60,000 IU",
        phone=phone,
        added_by="caretaker"
    )
    med = create_medication(req)
    assert med.approval_status == "pending_approval"
    assert med.added_by == "caretaker"

    # Elder approves it
    approved = approve_medication(med.id, phone=phone)
    assert approved.approval_status == "approved"

def test_elder_can_reject_unwanted_medicine_proposal():
    phone = "9849012345"
    req = CreateMedicationRequest(
        name="Experimental Supplement",
        timing_anchor="dinner",
        phone=phone,
        added_by="caretaker"
    )
    med = create_medication(req)
    assert med.approval_status == "pending_approval"

    # Elder rejects it
    del_res = reject_medication(med.id, phone=phone)
    assert del_res["status"] == "success"
    assert db.get_medication(med.id, phone=phone) is None

def test_adherence_insights_and_pattern_detection():
    insights = get_adherence_insights(phone="9849012345")
    assert "adherence_7_day_pct" in insights
    assert "adherence_30_day_pct" in insights
    assert "pattern_insight" in insights
    assert "refill_forecast" in insights
    assert insights["adherence_7_day_pct"] >= 80
