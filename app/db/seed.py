from datetime import datetime
from sqlalchemy.orm import Session
from app.config import settings
from app.db.models import (
    User, Patient, CaregiverLink, Routine, Medication,
    DoseLog, Alert, VoiceNote, Appointment, ActivityLog
)
from app.services.security_service import security_service

def seed_demo_data(db: Session):
    """
    Seeds Ramesh Rao demo profile only if DEMO_MODE=True.
    Idempotent: skips if demo user already exists.
    """
    if not settings.DEMO_MODE:
        return

    demo_phone = "9849012345"
    existing_user = db.query(User).filter(User.phone == demo_phone).first()
    if existing_user:
        return

    # 1. Create Patient User
    patient_user = User(
        id="u_ramesh_72",
        phone=demo_phone,
        name="Ramesh Rao",
        email="ramesh.rao@example.com",
        role="patient",
        hashed_passcode=security_service.hash_passcode("4321")
    )
    db.add(patient_user)

    # 2. Create Caregiver User
    caregiver_user = db.query(User).filter(User.phone == "9885099999").first()
    if not caregiver_user:
        caregiver_user = User(
            id="u_suresh_caregiver",
            phone="9885099999",
            name="Suresh Rao",
            email="suresh.rao@example.com",
            role="caregiver",
            hashed_passcode=security_service.hash_passcode("4321")
        )
        db.add(caregiver_user)

    db.flush()

    # 3. Create Patient Profile
    patient = Patient(
        id="p_ramesh_72",
        user_id=patient_user.id,
        name="Ramesh Rao",
        age=72,
        gender="Male",
        phone=demo_phone,
        emergency_contact="9885099999",
        language_preference="en",
        chronic_conditions=["High Blood Pressure (Hypertension)", "Sugar (Diabetes)", "Heart Condition"],
        allergies=["Penicillin"],
        doctor_name="Dr. K. S. Murthy",
        doctor_specialty="Cardiologist",
        doctor_hospital="Care Hospitals",
        doctor_phone="+91 40 2345 6789",
        share_doctor=True,
        share_hospital=True,
        share_conditions=True,
        share_meds=True,
        share_history=True
    )
    db.add(patient)
    db.flush()

    # 4. Routine
    routine = Routine(
        id="r_ramesh_72",
        patient_id=patient.id,
        wake_up="07:30",
        breakfast="09:00",
        lunch="13:30",
        dinner="20:30",
        bedtime="22:30",
        notes="Morning tea at 8:00, tiffin at 9:00"
    )
    db.add(routine)

    # 5. Caregiver Link
    caregiver_link = CaregiverLink(
        id="cl_suresh_ramesh",
        caregiver_user_id=caregiver_user.id,
        patient_id=patient.id,
        relationship_type="Son",
        status="approved",
        can_manage_meds=True,
        notify_missed_dose=True,
        notify_low_stock=True
    )
    db.add(caregiver_link)

    # 6. Medications
    meds = [
        Medication(
            id="m_telmisartan",
            patient_id=patient.id,
            brand_name="Telmikem 40",
            senior_label="BP Tablet",
            senior_label_te="BP మాత్ర",
            senior_label_hi="बीपी की गोली",
            salt_composition="Telmisartan 40mg",
            dosage="40mg (1 pill)",
            timing_anchor="breakfast",
            timing_relation="after_food",
            criticality="high",
            remaining_pills=2,
            daily_doses=1,
            pill_color="#EF4444",
            purpose="Blood Pressure",
            approval_status="approved",
            added_by="elder"
        ),
        Medication(
            id="m_metformin",
            patient_id=patient.id,
            brand_name="Glycomet 500",
            senior_label="Sugar Tablet",
            senior_label_te="షుగర్ మాత్ర",
            senior_label_hi="शुगर की गोली",
            salt_composition="Metformin 500mg",
            dosage="500mg (1 pill)",
            timing_anchor="breakfast",
            timing_relation="after_food",
            criticality="high",
            remaining_pills=18,
            daily_doses=2,
            pill_color="#3B82F6",
            purpose="Sugar Control",
            approval_status="approved",
            added_by="elder"
        ),
        Medication(
            id="m_ecosprin",
            patient_id=patient.id,
            brand_name="Ecosprin 75",
            senior_label="Heart & Blood Thinner",
            senior_label_te="గుండె / బ్లడ్ మాత్ర",
            senior_label_hi="दिल व खून पतला करने की गोली",
            salt_composition="Aspirin 75mg",
            dosage="75mg",
            timing_anchor="lunch",
            timing_relation="after_food",
            criticality="high",
            remaining_pills=14,
            daily_doses=1,
            pill_color="#F59E0B",
            purpose="Cardiovascular",
            approval_status="approved",
            added_by="elder"
        ),
        Medication(
            id="m_shelcal",
            patient_id=patient.id,
            brand_name="Shelcal 500",
            senior_label="Calcium & Bone Tablet",
            senior_label_te="ఎముకల కాల్షియం మాత్ర",
            senior_label_hi="कैल्शियम की गोली",
            salt_composition="Calcium + Vitamin D3",
            dosage="500mg",
            timing_anchor="lunch",
            timing_relation="after_food",
            criticality="low",
            remaining_pills=3,
            daily_doses=1,
            pill_color="#10B981",
            purpose="Bone Strength",
            approval_status="approved",
            added_by="elder"
        )
    ]
    for m in meds:
        db.add(m)

    # 7. Dose Log
    log = DoseLog(
        id="log_001",
        patient_id=patient.id,
        medication_id="m_telmisartan",
        medication_name="Telmikem 40",
        senior_label="BP Tablet",
        timing_anchor="breakfast",
        status="pending",
        logged_at=None,
        feedback_notes="Awaiting confirmation"
    )
    db.add(log)

    # 8. Alert
    alert = Alert(
        id="alt_01",
        patient_id=patient.id,
        severity="info",
        title="VayoCare Connected",
        message="Routine anchored to 09:00 AM Breakfast / Tiffin.",
        recipient_email="suresh.rao@example.com",
        status="delivered"
    )
    db.add(alert)

    # 9. Voice Note
    vn = VoiceNote(
        id="vn_1",
        patient_id=patient.id,
        caregiver_id=caregiver_user.id,
        caregiver_name="Suresh (Son)",
        message_text="Dad, please remember to take your morning BP and Sugar tablets after breakfast.",
        assigned_anchor="breakfast"
    )
    db.add(vn)

    # 10. Appointment
    appt = Appointment(
        id="appt_001",
        patient_id=patient.id,
        doctor_name="Dr. K. S. Murthy",
        specialty="Cardiologist",
        hospital="Care Hospitals",
        phone="+91 40 2345 6789",
        date="2026-11-20",
        time="10:30",
        notes="Quarterly cardiac routine evaluation",
        status="scheduled"
    )
    db.add(appt)

    # 11. Activity Log
    act = ActivityLog(
        id="act_01",
        patient_id=patient.id,
        actor_role="system",
        action="PROFILE_INITIALIZED",
        details="Ramesh Rao health circle securely initialized."
    )
    db.add(act)

    db.commit()
