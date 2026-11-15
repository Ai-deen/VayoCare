import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.models import (
    Patient, Caregiver, DoctorContact, RoutineSchedule,
    Medication, DoseLog, AlertNotification, CaregiverVoiceNote
)

class InMemoryDB:
    def __init__(self):
        self.patient: Patient = Patient(
            id="p_ramesh_72",
            name="Ramesh Rao",
            age=72,
            gender="Male",
            phone="9849012345",
            passcode="4321",
            language_preference="te",
            chronic_conditions=["High Blood Pressure (Hypertension)", "Sugar (Diabetes)", "Heart Condition"],
            allergies=["Penicillin"],
            routine=RoutineSchedule(
                wake_up="07:30",
                breakfast="09:00",
                lunch="13:30",
                dinner="20:30",
                bedtime="22:30",
                notes="Morning tea at 8:00, tiffin at 9:00"
            ),
            caregivers=[
                Caregiver(
                    id="c_suresh_1",
                    name="Suresh Rao",
                    relationship="Son",
                    phone="9885099999",
                    email="suresh.rao@example.com",
                    notify_missed_dose=True,
                    notify_low_stock=True
                ),
                Caregiver(
                    id="c_priya_2",
                    name="Dr. Priya Rao",
                    relationship="Daughter",
                    phone="9848088888",
                    email="priya.rao.md@example.com",
                    notify_missed_dose=True,
                    notify_low_stock=True
                )
            ],
            doctor=DoctorContact(
                name="Dr. K. S. Murthy",
                specialty="Cardiologist",
                hospital="Care Hospitals",
                phone="+91 40 2345 6789"
            ),
            voice_notes=[
                CaregiverVoiceNote(
                    id="vn_1",
                    caregiver_name="Suresh (Son)",
                    message_text="నాన్నగారు, ఉదయం టిఫిన్ అయ్యాక మీ BP మాత్ర, షుగర్ మాత్ర తప్పకుండా వేసుకోండి.",
                    created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    assigned_anchor="breakfast"
                )
            ]
        )

        self.medications: Dict[str, Medication] = {
            "m_telmisartan": Medication(
                id="m_telmisartan",
                brand_name="Telmikem 40",
                senior_label="BP Tablet",
                senior_label_te="BP మాత్ర",
                senior_label_hi="बीपी की गोली",
                salt_composition="Telmisartan 40mg",
                dosage="40mg (1 pill)",
                timing_anchor="breakfast",
                timing_relation="after_food",
                criticality="high",
                remaining_pills=2,  # Low stock runway alert demo!
                daily_doses=1,
                pill_color="#EF4444",
                purpose="Blood Pressure"
            ),
            "m_metformin": Medication(
                id="m_metformin",
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
                purpose="Sugar Control"
            ),
            "m_ecosprin": Medication(
                id="m_ecosprin",
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
                purpose="Cardiovascular"
            ),
            "m_shelcal": Medication(
                id="m_shelcal",
                brand_name="Shelcal 500",
                senior_label="Calcium & Bone Tablet",
                senior_label_te="ఎముకల కాల్షియం మాత్ర",
                senior_label_hi="कैल्शियम की गोली",
                salt_composition="Calcium + Vitamin D3",
                dosage="500mg",
                timing_anchor="lunch",
                timing_relation="after_food",
                criticality="low",
                remaining_pills=3,  # Low stock demo!
                daily_doses=1,
                pill_color="#10B981",
                purpose="Bone Strength"
            )
        }

        self.dose_logs: List[DoseLog] = [
            DoseLog(
                id="log_001",
                medication_id="m_telmisartan",
                medication_name="Telmikem 40",
                senior_label="BP Tablet",
                patient_id="p_ramesh_72",
                timing_anchor="breakfast",
                status="pending",
                logged_at=None,
                feedback_notes="Awaiting confirmation"
            ),
            DoseLog(
                id="log_002",
                medication_id="m_metformin",
                medication_name="Glycomet 500",
                senior_label="Sugar Tablet",
                patient_id="p_ramesh_72",
                timing_anchor="breakfast",
                status="pending",
                logged_at=None,
                feedback_notes="Awaiting confirmation"
            )
        ]

        self.alerts: List[AlertNotification] = [
            AlertNotification(
                id="alt_01",
                patient_id="p_ramesh_72",
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
                severity="info",
                title="VayoCare Connected",
                message="Routine anchored to 09:00 AM Breakfast / Tiffin.",
                recipient_email="suresh.rao@example.com",
                status="delivered"
            )
        ]

    def get_patient(self) -> Patient:
        return self.patient

    def update_patient_profile(self, name: str, phone: str, role: str) -> Patient:
        self.patient.name = name
        self.patient.phone = phone
        return self.patient

    def add_caregiver_voice_note(self, caregiver_name: str, message: str, anchor: str = "breakfast") -> CaregiverVoiceNote:
        note = CaregiverVoiceNote(
            id=f"vn_{int(datetime.now().timestamp())}",
            caregiver_name=caregiver_name,
            message_text=message,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
            assigned_anchor=anchor
        )
        self.patient.voice_notes.insert(0, note)
        return note

    def update_routine(self, schedule: RoutineSchedule) -> RoutineSchedule:
        self.patient.routine = schedule
        return self.patient.routine

    def get_medications(self) -> List[Medication]:
        return list(self.medications.values())

    def get_medication(self, med_id: str) -> Optional[Medication]:
        return self.medications.get(med_id)

    def log_dose(self, med_id: str, status: str, notes: str = "", triage: str = "none") -> Optional[DoseLog]:
        med = self.get_medication(med_id)
        if not med:
            return None

        if status == "taken" and med.remaining_pills > 0:
            med.remaining_pills -= 1

        new_log = DoseLog(
            id=f"log_{int(datetime.now().timestamp()*1000)}",
            medication_id=med_id,
            medication_name=med.brand_name,
            senior_label=med.senior_label,
            patient_id=self.patient.id,
            timing_anchor=med.timing_anchor,
            status=status,
            logged_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            feedback_notes=notes,
            triage_action=triage
        )
        self.dose_logs.insert(0, new_log)
        return new_log

    def get_today_logs(self) -> List[DoseLog]:
        return self.dose_logs

    def add_alert(self, severity: str, title: str, message: str, recipient: str = "suresh.rao@example.com") -> AlertNotification:
        alert = AlertNotification(
            id=f"alt_{int(datetime.now().timestamp()*1000)}",
            patient_id=self.patient.id,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
            severity=severity,
            title=title,
            message=message,
            recipient_email=recipient,
            status="sent"
        )
        self.alerts.insert(0, alert)
        return alert

    def get_alerts(self) -> List[AlertNotification]:
        return self.alerts

db = InMemoryDB()
