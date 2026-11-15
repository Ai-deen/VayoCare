import os
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.models import (
    Patient, Caregiver, DoctorContact, RoutineSchedule,
    Medication, DoseLog, AlertNotification, CaregiverVoiceNote,
    Appointment, ActivityLog
)
from app.services.security_service import security_service

DATA_FILE = "vayocare_db.json"

class MultiUserDB:
    def __init__(self):
        self.patients: Dict[str, Patient] = {}
        self.medications: Dict[str, Dict[str, Medication]] = {}
        self.dose_logs: Dict[str, List[DoseLog]] = {}
        self.alerts: Dict[str, List[AlertNotification]] = {}
        self.active_phone: str = "9849012345"
        
        self._init_demo_patient()
        self._load_from_disk()

    def _init_demo_patient(self):
        demo_phone = "9849012345"
        self.patients[demo_phone] = Patient(
            id="p_ramesh_72",
            name="Ramesh Rao",
            age=72,
            gender="Male",
            phone=demo_phone,
            passcode=security_service.hash_passcode("4321"),
            language_preference="en",
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
                    role="caregiver",
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
                    message_text="Dad, please remember to take your morning BP and Sugar tablets after breakfast.",
                    created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    assigned_anchor="breakfast"
                )
            ],
            appointments=[
                Appointment(
                    id="appt_001",
                    doctor_name="Dr. K. S. Murthy",
                    specialty="Cardiologist",
                    hospital="Care Hospitals",
                    phone="+91 40 2345 6789",
                    date="2026-11-20",
                    time="10:30",
                    notes="Quarterly cardiac routine evaluation",
                    status="scheduled"
                )
            ],
            activity_logs=[
                ActivityLog(
                    id="act_01",
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    actor_role="system",
                    action="PROFILE_INITIALIZED",
                    details="Ramesh Rao health circle securely initialized."
                )
            ]
        )

        self.medications[demo_phone] = {
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
                remaining_pills=2,
                daily_doses=1,
                pill_color="#EF4444",
                purpose="Blood Pressure",
                approval_status="approved",
                added_by="elder"
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
                purpose="Sugar Control",
                approval_status="approved",
                added_by="elder"
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
                purpose="Cardiovascular",
                approval_status="approved",
                added_by="elder"
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
                remaining_pills=3,
                daily_doses=1,
                pill_color="#10B981",
                purpose="Bone Strength",
                approval_status="approved",
                added_by="elder"
            )
        }

        self.dose_logs[demo_phone] = [
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
            )
        ]

        self.alerts[demo_phone] = [
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

    def _save_to_disk(self):
        try:
            data = {
                "patients": {p: pat.model_dump() for p, pat in self.patients.items()},
                "medications": {p: {mid: m.model_dump() for mid, m in meds.items()} for p, meds in self.medications.items()},
                "dose_logs": {p: [l.model_dump() for l in logs] for p, logs in self.dose_logs.items()},
                "alerts": {p: [a.model_dump() for a in alts] for p, alts in self.alerts.items()}
            }
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, default=str)
        except Exception:
            pass

    def _load_from_disk(self):
        if not os.path.exists(DATA_FILE):
            return
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for p, pdata in data.get("patients", {}).items():
                self.patients[p] = Patient(**pdata)
            for p, mdict in data.get("medications", {}).items():
                self.medications[p] = {mid: Medication(**mdata) for mid, mdata in mdict.items()}
            for p, llist in data.get("dose_logs", {}).items():
                self.dose_logs[p] = [DoseLog(**ldata) for ldata in llist]
            for p, alist in data.get("alerts", {}).items():
                self.alerts[p] = [AlertNotification(**adata) for adata in alist]
        except Exception:
            pass

    def _normalize_phone(self, phone: Any) -> str:
        if not phone or not isinstance(phone, str):
            return self.active_phone
        clean = "".join(c for c in phone if c.isdigit())
        return clean or self.active_phone

    def get_patient(self, phone: Optional[str] = None) -> Patient:
        p_key = self._normalize_phone(phone)
        if p_key in self.patients:
            return self.patients[p_key]
        for pat in self.patients.values():
            if pat.id == phone or pat.phone == phone:
                return pat
        return self.patients.get(self.active_phone, list(self.patients.values())[0])

    def get_or_create_patient(self, phone: str, name: str = "", role: str = "patient") -> Patient:
        clean = self._normalize_phone(phone)
        self.active_phone = clean
        if clean in self.patients:
            pat = self.patients[clean]
            if name and (pat.name == "Senior Patient" or not pat.name):
                pat.name = name
            return pat

        new_pat = Patient(
            id=f"p_{clean}",
            name=name or "Senior Patient",
            age=70,
            gender="Not Specified",
            phone=clean,
            passcode=security_service.hash_passcode("1234"),
            language_preference="en",
            chronic_conditions=[],
            allergies=[],
            routine=RoutineSchedule(
                wake_up="07:30",
                breakfast="09:00",
                lunch="13:30",
                dinner="20:30",
                bedtime="22:00",
                notes="Configured during onboarding"
            ),
            caregivers=[],
            doctor=DoctorContact(
                name="Primary Doctor",
                specialty="General Physician",
                hospital="Local Clinic",
                phone=""
            ),
            voice_notes=[],
            appointments=[],
            activity_logs=[
                ActivityLog(
                    id=f"act_{int(datetime.now().timestamp())}",
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    actor_role=role,
                    action="ACCOUNT_CREATED",
                    details=f"Patient account {clean} created."
                )
            ]
        )
        self.patients[clean] = new_pat
        self.medications[clean] = {}
        self.dose_logs[clean] = []
        self.alerts[clean] = []
        self._save_to_disk()
        return new_pat

    def add_activity_log(self, phone: str, actor_role: str, action: str, details: str):
        pat = self.get_patient(phone)
        log = ActivityLog(
            id=f"act_{int(datetime.now().timestamp()*1000)}",
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            actor_role=actor_role,
            action=action,
            details=details
        )
        pat.activity_logs.insert(0, log)
        self._save_to_disk()
        return log

    def get_activity_logs(self, phone: Optional[str] = None) -> List[ActivityLog]:
        pat = self.get_patient(phone)
        return pat.activity_logs

    def update_routine(self, schedule: RoutineSchedule, phone: Optional[str] = None) -> RoutineSchedule:
        patient = self.get_patient(phone)
        patient.routine = schedule
        self.add_activity_log(patient.phone, "elder", "ROUTINE_UPDATED", f"Breakfast: {schedule.breakfast}, Lunch: {schedule.lunch}, Dinner: {schedule.dinner}")
        self._save_to_disk()
        return patient.routine

    def add_caregiver_voice_note(self, caregiver_name: str, message: str, anchor: str = "breakfast", phone: Optional[str] = None) -> CaregiverVoiceNote:
        patient = self.get_patient(phone)
        note = CaregiverVoiceNote(
            id=f"vn_{int(datetime.now().timestamp())}",
            caregiver_name=caregiver_name,
            message_text=message,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
            assigned_anchor=anchor
        )
        patient.voice_notes.insert(0, note)
        self.add_activity_log(patient.phone, "caretaker", "VOICE_NOTE_SENT", f"{caregiver_name} added a voice note for {anchor}.")
        self._save_to_disk()
        return note

    def get_medications(self, phone: Optional[str] = None) -> List[Medication]:
        p_key = self._normalize_phone(phone)
        if p_key in self.medications and len(self.medications[p_key]) > 0:
            return list(self.medications[p_key].values())
        return list(self.medications.get("9849012345", {}).values())

    def add_medication(self, med: Medication, phone: Optional[str] = None) -> Medication:
        p_key = self._normalize_phone(phone)
        if p_key not in self.medications:
            self.medications[p_key] = {}
        self.medications[p_key][med.id] = med
        self.add_activity_log(p_key, med.added_by, "MEDICATION_ADDED", f"{med.senior_label} ({med.brand_name}) added [Status: {med.approval_status}].")
        self._save_to_disk()
        return med

    def approve_medication(self, med_id: str, phone: Optional[str] = None) -> Optional[Medication]:
        p_key = self._normalize_phone(phone)
        meds = self.medications.get(p_key, {})
        if med_id in meds:
            meds[med_id].approval_status = "approved"
            self.add_activity_log(p_key, "elder", "MEDICATION_APPROVED", f"Elder approved medication: {meds[med_id].senior_label}.")
            self._save_to_disk()
            return meds[med_id]
        return None

    def reject_medication(self, med_id: str, phone: Optional[str] = None) -> bool:
        p_key = self._normalize_phone(phone)
        meds = self.medications.get(p_key, {})
        if med_id in meds:
            lbl = meds[med_id].senior_label
            del meds[med_id]
            self.add_activity_log(p_key, "elder", "MEDICATION_REJECTED", f"Elder declined medication proposal: {lbl}.")
            self._save_to_disk()
            return True
        return False

    def get_medication(self, med_id: str, phone: Optional[str] = None) -> Optional[Medication]:
        p_key = self._normalize_phone(phone)
        meds = self.medications.get(p_key, {})
        if med_id in meds:
            return meds[med_id]
        return self.medications.get("9849012345", {}).get(med_id)

    def log_dose(self, med_id: str, status: str, notes: str = "", triage: str = "none", phone: Optional[str] = None) -> Optional[DoseLog]:
        p_key = self._normalize_phone(phone)
        patient = self.get_patient(p_key)
        med = self.get_medication(med_id, p_key)
        
        med_name = med.brand_name if med else med_id
        senior_lbl = med.senior_label if med else med_id
        anchor = med.timing_anchor if med else "breakfast"

        if med and status == "taken" and med.remaining_pills > 0:
            med.remaining_pills -= 1

        new_log = DoseLog(
            id=f"log_{int(datetime.now().timestamp()*1000)}",
            medication_id=med_id,
            medication_name=med_name,
            senior_label=senior_lbl,
            patient_id=patient.id,
            timing_anchor=anchor,
            status=status,
            logged_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            feedback_notes=notes,
            triage_action=triage
        )

        if p_key not in self.dose_logs:
            self.dose_logs[p_key] = []
        self.dose_logs[p_key].insert(0, new_log)
        self.add_activity_log(p_key, "elder", f"DOSE_{status.upper()}", f"{senior_lbl} logged as {status}.")
        self._save_to_disk()
        return new_log

    def get_today_logs(self, phone: Optional[str] = None) -> List[DoseLog]:
        p_key = self._normalize_phone(phone)
        return self.dose_logs.get(p_key, self.dose_logs.get(self.active_phone, []))

    # Appointments CRUD
    def add_appointment(self, appt: Appointment, phone: Optional[str] = None) -> Appointment:
        pat = self.get_patient(phone)
        pat.appointments.append(appt)
        self.add_activity_log(pat.phone, "caretaker", "APPOINTMENT_SCHEDULED", f"Appointment with {appt.doctor_name} on {appt.date} at {appt.time}.")
        self._save_to_disk()
        return appt

    def get_appointments(self, phone: Optional[str] = None) -> List[Appointment]:
        pat = self.get_patient(phone)
        return getattr(pat, 'appointments', [])

    def delete_appointment(self, appt_id: str, phone: Optional[str] = None) -> bool:
        pat = self.get_patient(phone)
        initial_len = len(pat.appointments)
        pat.appointments = [a for a in pat.appointments if a.id != appt_id]
        if len(pat.appointments) < initial_len:
            self.add_activity_log(pat.phone, "caretaker", "APPOINTMENT_CANCELLED", f"Appointment {appt_id} cancelled.")
            self._save_to_disk()
            return True
        return False

    def add_alert(self, severity: str, title: str, message: str, recipient: str = "caregiver@example.com", phone: Optional[str] = None) -> AlertNotification:
        p_key = self._normalize_phone(phone)
        patient = self.get_patient(p_key)
        alert = AlertNotification(
            id=f"alt_{int(datetime.now().timestamp()*1000)}",
            patient_id=patient.id,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
            severity=severity,
            title=title,
            message=message,
            recipient_email=recipient,
            status="sent"
        )
        if p_key not in self.alerts:
            self.alerts[p_key] = []
        self.alerts[p_key].insert(0, alert)
        self._save_to_disk()
        return alert

    def get_alerts(self, phone: Optional[str] = None) -> List[AlertNotification]:
        p_key = self._normalize_phone(phone)
        return self.alerts.get(p_key, self.alerts.get(self.active_phone, []))

db = MultiUserDB()
