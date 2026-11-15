import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from app.config import settings
from app.db.session import SessionLocal, init_db
from app.db.seed import seed_demo_data
from app.db import models as db_models
from app.models import (
    Patient, Caregiver, DoctorContact, RoutineSchedule,
    Medication, DoseLog, AlertNotification, CaregiverVoiceNote,
    Appointment, ActivityLog
)
from app.services.security_service import security_service

class MultiUserDB:
    def __init__(self):
        # Initialize schema and seed demo data only when DEMO_MODE is true
        init_db()
        with SessionLocal() as session:
            seed_demo_data(session)

    def _normalize_phone(self, phone: Any) -> str:
        if not phone or not isinstance(phone, str):
            return ""
        return "".join(c for c in phone if c.isdigit())

    def _convert_db_patient_to_pydantic(self, p: db_models.Patient, session) -> Patient:
        # Load caregivers via caregiver_links
        caregivers = []
        for link in p.caregiver_links:
            cg_user = link.caregiver_user
            caregivers.append(
                Caregiver(
                    id=link.id,
                    name=cg_user.name if cg_user else "Caregiver",
                    relationship=getattr(link, "relationship_type", "Caregiver") or "Caregiver",
                    phone=cg_user.phone if cg_user else "",
                    email=cg_user.email or "",
                    role="caregiver",
                    notify_missed_dose=link.notify_missed_dose,
                    notify_low_stock=link.notify_low_stock
                )
            )

        # Routine
        routine_obj = RoutineSchedule()
        if p.routine:
            routine_obj = RoutineSchedule(
                wake_up=p.routine.wake_up or "07:30",
                breakfast=p.routine.breakfast or "09:00",
                lunch=p.routine.lunch or "13:30",
                dinner=p.routine.dinner or "20:30",
                bedtime=p.routine.bedtime or "22:00",
                notes=p.routine.notes or ""
            )

        # Doctor
        doc_obj = DoctorContact(
            name=p.doctor_name or "Primary Doctor",
            specialty=p.doctor_specialty or "General Physician",
            hospital=p.doctor_hospital or "Local Clinic",
            phone=p.doctor_phone or ""
        )

        # Voice notes
        v_notes = [
            CaregiverVoiceNote(
                id=vn.id,
                caregiver_name=vn.caregiver_name,
                message_text=vn.message_text,
                audio_url=vn.audio_url,
                created_at=vn.created_at.strftime("%Y-%m-%d %H:%M") if vn.created_at else "",
                assigned_anchor=vn.assigned_anchor or "breakfast"
            ) for vn in p.voice_notes
        ]

        # Appointments
        appts = [
            Appointment(
                id=apt.id,
                doctor_name=apt.doctor_name,
                specialty=apt.specialty,
                hospital=apt.hospital,
                phone=apt.phone or "",
                date=apt.date,
                time=apt.time,
                notes=apt.notes or "",
                status=apt.status or "scheduled"
            ) for apt in p.appointments
        ]

        # Activity logs
        acts = [
            ActivityLog(
                id=act.id,
                timestamp=act.timestamp.strftime("%Y-%m-%d %H:%M:%S") if act.timestamp else "",
                actor_role=act.actor_role,
                action=act.action,
                details=act.details or ""
            ) for act in sorted(p.activity_logs, key=lambda x: x.timestamp or datetime.min, reverse=True)
        ]

        # Passcode from user
        user_passcode = p.user.hashed_passcode if p.user else security_service.hash_passcode("1234")

        return Patient(
            id=p.id,
            name=p.name,
            age=p.age or 70,
            gender=p.gender or "Not Specified",
            phone=p.phone,
            passcode=user_passcode,
            language_preference=p.language_preference or "en",
            chronic_conditions=p.chronic_conditions or [],
            allergies=p.allergies or [],
            routine=routine_obj,
            caregivers=caregivers,
            doctor=doc_obj,
            voice_notes=v_notes,
            appointments=appts,
            activity_logs=acts
        )

    def get_patient(self, phone: Optional[str] = None) -> Patient:
        with SessionLocal() as session:
            if phone and isinstance(phone, str):
                clean = "".join(c for c in phone if c.isdigit())
                p = session.query(db_models.Patient).filter(
                    (db_models.Patient.phone == clean) | (db_models.Patient.id == phone)
                ).first()
                if p:
                    return self._convert_db_patient_to_pydantic(p, session)

            # When phone is not provided, check demo patient first if DEMO_MODE
            if settings.DEMO_MODE:
                demo = session.query(db_models.Patient).filter(db_models.Patient.phone == "9849012345").first()
                if demo:
                    return self._convert_db_patient_to_pydantic(demo, session)
            
            clean = self._normalize_phone(phone)
            p = session.query(db_models.Patient).filter(
                (db_models.Patient.phone == clean) | (db_models.Patient.id == phone)
            ).first()
            if p:
                return self._convert_db_patient_to_pydantic(p, session)
            
            # Or first patient
            first_p = session.query(db_models.Patient).first()
            if first_p:
                return self._convert_db_patient_to_pydantic(first_p, session)

            return self.get_or_create_patient(clean)

    def get_or_create_patient(self, phone: str, name: str = "", role: str = "patient") -> Patient:
        clean = self._normalize_phone(phone)
        self.active_phone = clean
        with SessionLocal() as session:
            p = session.query(db_models.Patient).filter(db_models.Patient.phone == clean).first()
            if p:
                if name and (p.name == "Senior Patient" or not p.name):
                    p.name = name
                    session.commit()
                return self._convert_db_patient_to_pydantic(p, session)

            # Create User if not exists
            user = session.query(db_models.User).filter(db_models.User.phone == clean).first()
            if not user:
                user = db_models.User(
                    id=f"u_{clean}",
                    phone=clean,
                    name=name or "Senior Patient",
                    role=role,
                    hashed_passcode=security_service.hash_passcode(uuid.uuid4().hex[:10])
                )
                session.add(user)
                session.flush()

            new_pat = db_models.Patient(
                id=f"p_{clean}",
                user_id=user.id,
                name=name or "Senior Patient",
                age=70,
                gender="Not Specified",
                phone=clean,
                language_preference="en",
                chronic_conditions=[],
                allergies=[],
                doctor_name="Primary Doctor",
                doctor_specialty="General Physician",
                doctor_hospital="Local Clinic"
            )
            session.add(new_pat)
            session.flush()

            # Create initial routine
            routine = db_models.Routine(
                id=f"r_{clean}",
                patient_id=new_pat.id,
                wake_up="07:30",
                breakfast="09:00",
                lunch="13:30",
                dinner="20:30",
                bedtime="22:00",
                notes="Configured during onboarding"
            )
            session.add(routine)

            # Create initial activity log
            act = db_models.ActivityLog(
                id=f"act_{uuid.uuid4().hex}",
                patient_id=new_pat.id,
                actor_role=role,
                action="ACCOUNT_CREATED",
                details=f"Patient account {clean} created.",
                timestamp=datetime.now()
            )
            session.add(act)
            session.commit()
            return self._convert_db_patient_to_pydantic(new_pat, session)

    def add_activity_log(self, phone: str, actor_role: str, action: str, details: str):
        clean = self._normalize_phone(phone)
        with SessionLocal() as session:
            p = session.query(db_models.Patient).filter(
                (db_models.Patient.phone == clean) | (db_models.Patient.id == clean)
            ).first()
            if not p:
                p = session.query(db_models.Patient).filter(db_models.Patient.phone == self.active_phone).first()
            if p:
                act = db_models.ActivityLog(
                    id=f"act_{uuid.uuid4().hex}",
                    patient_id=p.id,
                    actor_role=actor_role,
                    action=action,
                    details=details,
                    timestamp=datetime.now()
                )
                session.add(act)
                session.commit()
                return ActivityLog(
                    id=act.id,
                    timestamp=act.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    actor_role=act.actor_role,
                    action=act.action,
                    details=act.details
                )
        return None

    def get_activity_logs(self, phone: Optional[str] = None) -> List[ActivityLog]:
        pat = self.get_patient(phone)
        return pat.activity_logs

    def update_routine(self, schedule: RoutineSchedule, phone: Optional[str] = None) -> RoutineSchedule:
        clean = self._normalize_phone(phone)
        with SessionLocal() as session:
            p = session.query(db_models.Patient).filter(
                (db_models.Patient.phone == clean) | (db_models.Patient.id == clean)
            ).first()
            if not p:
                p = session.query(db_models.Patient).first()
            if p:
                if not p.routine:
                    p.routine = db_models.Routine(patient_id=p.id)
                p.routine.wake_up = schedule.wake_up
                p.routine.breakfast = schedule.breakfast
                p.routine.lunch = schedule.lunch
                p.routine.dinner = schedule.dinner
                p.routine.bedtime = schedule.bedtime
                p.routine.notes = schedule.notes
                session.commit()
                self.add_activity_log(p.phone, "elder", "ROUTINE_UPDATED", f"Breakfast: {schedule.breakfast}, Lunch: {schedule.lunch}, Dinner: {schedule.dinner}")
        return schedule

    def add_caregiver_voice_note(self, caregiver_name: str, message: str, anchor: str = "breakfast", phone: Optional[str] = None) -> CaregiverVoiceNote:
        clean = self._normalize_phone(phone)
        with SessionLocal() as session:
            p = session.query(db_models.Patient).filter(
                (db_models.Patient.phone == clean) | (db_models.Patient.id == clean)
            ).first()
            if not p:
                p = session.query(db_models.Patient).first()
            vn = db_models.VoiceNote(
                id=f"vn_{uuid.uuid4().hex}",
                patient_id=p.id if p else "p_ramesh_72",
                caregiver_name=caregiver_name,
                message_text=message,
                assigned_anchor=anchor,
                created_at=datetime.now()
            )
            session.add(vn)
            session.commit()
            if p:
                self.add_activity_log(p.phone, "caretaker", "VOICE_NOTE_SENT", f"{caregiver_name} added a voice note for {anchor}.")
            return CaregiverVoiceNote(
                id=vn.id,
                caregiver_name=vn.caregiver_name,
                message_text=vn.message_text,
                audio_url=vn.audio_url,
                created_at=vn.created_at.strftime("%Y-%m-%d %H:%M"),
                assigned_anchor=vn.assigned_anchor
            )

    def get_medications(self, phone: Optional[str] = None) -> List[Medication]:
        with SessionLocal() as session:
            p = None
            if phone and isinstance(phone, str):
                clean = "".join(c for c in phone if c.isdigit())
                p = session.query(db_models.Patient).filter(
                    (db_models.Patient.phone == clean) | (db_models.Patient.id == phone)
                ).first()
            elif settings.DEMO_MODE:
                p = session.query(db_models.Patient).filter(db_models.Patient.phone == "9849012345").first()
            
            if not p:
                clean = self._normalize_phone(phone)
                p = session.query(db_models.Patient).filter(
                    (db_models.Patient.phone == clean) | (db_models.Patient.id == clean)
                ).first()
            if not p and settings.DEMO_MODE:
                p = session.query(db_models.Patient).filter(db_models.Patient.phone == "9849012345").first()

            if p:
                meds = session.query(db_models.Medication).filter(db_models.Medication.patient_id == p.id).all()
                if meds or phone:
                    return [
                        Medication(
                            id=m.id,
                            brand_name=m.brand_name,
                            senior_label=m.senior_label,
                            senior_label_te=m.senior_label_te or "",
                            senior_label_hi=m.senior_label_hi or "",
                            salt_composition=m.salt_composition or "",
                            dosage=m.dosage,
                            timing_anchor=m.timing_anchor,
                            timing_relation=m.timing_relation or "after_food",
                            criticality=m.criticality or "high",
                            remaining_pills=m.remaining_pills or 0,
                            daily_doses=m.daily_doses or 1,
                            pill_color=m.pill_color or "#3B82F6",
                            purpose=m.purpose or "",
                            approval_status=m.approval_status or "approved",
                            added_by=m.added_by or "elder"
                        ) for m in meds
                    ]
            
            # If still empty and in demo mode, return demo medications
            if settings.DEMO_MODE:
                demo_p = session.query(db_models.Patient).filter(db_models.Patient.phone == "9849012345").first()
                if demo_p:
                    demo_meds = session.query(db_models.Medication).filter(db_models.Medication.patient_id == demo_p.id).all()
                    return [
                        Medication(
                            id=m.id,
                            brand_name=m.brand_name,
                            senior_label=m.senior_label,
                            senior_label_te=m.senior_label_te or "",
                            senior_label_hi=m.senior_label_hi or "",
                            salt_composition=m.salt_composition or "",
                            dosage=m.dosage,
                            timing_anchor=m.timing_anchor,
                            timing_relation=m.timing_relation or "after_food",
                            criticality=m.criticality or "high",
                            remaining_pills=m.remaining_pills or 0,
                            daily_doses=m.daily_doses or 1,
                            pill_color=m.pill_color or "#3B82F6",
                            purpose=m.purpose or "",
                            approval_status=m.approval_status or "approved",
                            added_by=m.added_by or "elder"
                        ) for m in demo_meds
                    ]
            return []

    def add_medication(self, med: Medication, phone: Optional[str] = None) -> Medication:
        clean = self._normalize_phone(phone)
        with SessionLocal() as session:
            p = session.query(db_models.Patient).filter(
                (db_models.Patient.phone == clean) | (db_models.Patient.id == clean)
            ).first()
            if not p:
                self.get_or_create_patient(clean)
                p = session.query(db_models.Patient).filter(db_models.Patient.phone == clean).first()
            
            db_med = session.query(db_models.Medication).filter(
                db_models.Medication.id == med.id,
                db_models.Medication.patient_id == p.id
            ).first()

            if not db_med:
                db_med = db_models.Medication(
                    id=med.id,
                    patient_id=p.id,
                    brand_name=med.brand_name,
                    senior_label=med.senior_label,
                    senior_label_te=med.senior_label_te,
                    senior_label_hi=med.senior_label_hi,
                    salt_composition=med.salt_composition,
                    dosage=med.dosage,
                    timing_anchor=med.timing_anchor,
                    timing_relation=med.timing_relation,
                    criticality=med.criticality,
                    remaining_pills=med.remaining_pills,
                    daily_doses=med.daily_doses,
                    pill_color=med.pill_color,
                    purpose=med.purpose,
                    approval_status=med.approval_status,
                    added_by=med.added_by
                )
                session.add(db_med)
            else:
                db_med.brand_name = med.brand_name
                db_med.senior_label = med.senior_label
                db_med.senior_label_te = med.senior_label_te
                db_med.senior_label_hi = med.senior_label_hi
                db_med.salt_composition = med.salt_composition
                db_med.dosage = med.dosage
                db_med.timing_anchor = med.timing_anchor
                db_med.timing_relation = med.timing_relation
                db_med.criticality = med.criticality
                db_med.remaining_pills = med.remaining_pills
                db_med.daily_doses = med.daily_doses
                db_med.pill_color = med.pill_color
                db_med.purpose = med.purpose
                db_med.approval_status = med.approval_status
                db_med.added_by = med.added_by

            session.commit()
            self.add_activity_log(clean, med.added_by, "MEDICATION_ADDED", f"{med.senior_label} ({med.brand_name}) added [Status: {med.approval_status}].")
            return med

    def approve_medication(self, med_id: str, phone: Optional[str] = None) -> Optional[Medication]:
        clean = self._normalize_phone(phone)
        with SessionLocal() as session:
            p = session.query(db_models.Patient).filter(
                (db_models.Patient.phone == clean) | (db_models.Patient.id == clean)
            ).first()
            if p:
                db_med = session.query(db_models.Medication).filter(
                    db_models.Medication.id == med_id,
                    db_models.Medication.patient_id == p.id
                ).first()
                if db_med:
                    db_med.approval_status = "approved"
                    session.commit()
                    self.add_activity_log(clean, "elder", "MEDICATION_APPROVED", f"Elder approved medication: {db_med.senior_label}.")
                    return Medication(
                        id=db_med.id,
                        brand_name=db_med.brand_name,
                        senior_label=db_med.senior_label,
                        salt_composition=db_med.salt_composition or "",
                        dosage=db_med.dosage,
                        timing_anchor=db_med.timing_anchor,
                        approval_status="approved",
                        remaining_pills=db_med.remaining_pills
                    )
        return None

    def reject_medication(self, med_id: str, phone: Optional[str] = None) -> bool:
        clean = self._normalize_phone(phone)
        with SessionLocal() as session:
            p = session.query(db_models.Patient).filter(
                (db_models.Patient.phone == clean) | (db_models.Patient.id == clean)
            ).first()
            if p:
                db_med = session.query(db_models.Medication).filter(
                    db_models.Medication.id == med_id,
                    db_models.Medication.patient_id == p.id
                ).first()
                if db_med:
                    lbl = db_med.senior_label
                    session.delete(db_med)
                    session.commit()
                    self.add_activity_log(clean, "elder", "MEDICATION_REJECTED", f"Elder declined medication proposal: {lbl}.")
                    return True
        return False

    def get_medication(self, med_id: str, phone: Optional[str] = None) -> Optional[Medication]:
        clean = self._normalize_phone(phone)
        with SessionLocal() as session:
            p = session.query(db_models.Patient).filter(
                (db_models.Patient.phone == clean) | (db_models.Patient.id == clean)
            ).first()
            db_med = None
            if p:
                db_med = session.query(db_models.Medication).filter(
                    db_models.Medication.id == med_id,
                    db_models.Medication.patient_id == p.id
                ).first()
            if not db_med:
                db_med = session.query(db_models.Medication).filter(db_models.Medication.id == med_id).first()
            
            if db_med:
                return Medication(
                    id=db_med.id,
                    brand_name=db_med.brand_name,
                    senior_label=db_med.senior_label,
                    senior_label_te=db_med.senior_label_te or "",
                    senior_label_hi=db_med.senior_label_hi or "",
                    salt_composition=db_med.salt_composition or "",
                    dosage=db_med.dosage,
                    timing_anchor=db_med.timing_anchor,
                    timing_relation=db_med.timing_relation or "after_food",
                    criticality=db_med.criticality or "high",
                    remaining_pills=db_med.remaining_pills or 0,
                    daily_doses=db_med.daily_doses or 1,
                    pill_color=db_med.pill_color or "#3B82F6",
                    purpose=db_med.purpose or "",
                    approval_status=db_med.approval_status or "approved",
                    added_by=db_med.added_by or "elder"
                )
        return None

    def log_dose(self, med_id: str, status: str, notes: str = "", triage: str = "none", phone: Optional[str] = None) -> Optional[DoseLog]:
        clean = self._normalize_phone(phone)
        with SessionLocal() as session:
            p = session.query(db_models.Patient).filter(
                (db_models.Patient.phone == clean) | (db_models.Patient.id == clean)
            ).first()
            if not p:
                p = session.query(db_models.Patient).first()
            
            med = None
            if p:
                med = session.query(db_models.Medication).filter(
                    db_models.Medication.id == med_id,
                    db_models.Medication.patient_id == p.id
                ).first()
            if not med:
                med = session.query(db_models.Medication).filter(db_models.Medication.id == med_id).first()

            med_name = med.brand_name if med else med_id
            senior_lbl = med.senior_label if med else med_id
            anchor = med.timing_anchor if med else "breakfast"

            if med and status == "taken" and med.remaining_pills > 0:
                med.remaining_pills -= 1

            new_log = db_models.DoseLog(
                id=f"log_{uuid.uuid4().hex}",
                medication_id=med_id,
                medication_name=med_name,
                senior_label=senior_lbl,
                patient_id=p.id if p else "p_ramesh_72",
                timing_anchor=anchor,
                status=status,
                logged_at=datetime.now(),
                feedback_notes=notes,
                triage_action=triage
            )
            session.add(new_log)
            session.commit()

            if p:
                self.add_activity_log(p.phone, "elder", f"DOSE_{status.upper()}", f"{senior_lbl} logged as {status}.")

            return DoseLog(
                id=new_log.id,
                medication_id=med_id,
                medication_name=med_name,
                senior_label=senior_lbl,
                patient_id=new_log.patient_id,
                timing_anchor=anchor,
                status=status,
                logged_at=new_log.logged_at.strftime("%Y-%m-%d %H:%M:%S") if new_log.logged_at else None,
                feedback_notes=notes,
                triage_action=triage
            )

    def get_today_logs(self, phone: Optional[str] = None) -> List[DoseLog]:
        clean = self._normalize_phone(phone)
        with SessionLocal() as session:
            p = session.query(db_models.Patient).filter(
                (db_models.Patient.phone == clean) | (db_models.Patient.id == clean)
            ).first()
            if not p and settings.DEMO_MODE:
                p = session.query(db_models.Patient).filter(db_models.Patient.phone == "9849012345").first()
            if p:
                logs = session.query(db_models.DoseLog).filter(
                    db_models.DoseLog.patient_id == p.id
                ).order_by(db_models.DoseLog.created_at.desc()).all()
                return [
                    DoseLog(
                        id=l.id,
                        medication_id=l.medication_id,
                        medication_name=l.medication_name,
                        senior_label=l.senior_label,
                        patient_id=l.patient_id,
                        timing_anchor=l.timing_anchor,
                        status=l.status,
                        logged_at=l.logged_at.strftime("%Y-%m-%d %H:%M:%S") if l.logged_at else None,
                        feedback_notes=l.feedback_notes or "",
                        triage_action=l.triage_action or "none"
                    ) for l in logs
                ]
            return []

    # Appointments CRUD
    def add_appointment(self, appt: Appointment, phone: Optional[str] = None) -> Appointment:
        clean = self._normalize_phone(phone)
        with SessionLocal() as session:
            p = session.query(db_models.Patient).filter(
                (db_models.Patient.phone == clean) | (db_models.Patient.id == clean)
            ).first()
            if not p:
                p = session.query(db_models.Patient).first()
            
            db_appt = db_models.Appointment(
                id=appt.id,
                patient_id=p.id if p else "p_ramesh_72",
                doctor_name=appt.doctor_name,
                specialty=appt.specialty,
                hospital=appt.hospital,
                phone=appt.phone or "",
                date=appt.date,
                time=appt.time,
                notes=appt.notes or "",
                status=appt.status or "scheduled"
            )
            session.add(db_appt)
            session.commit()
            if p:
                self.add_activity_log(p.phone, "caretaker", "APPOINTMENT_SCHEDULED", f"Appointment with {appt.doctor_name} on {appt.date} at {appt.time}.")
        return appt

    def get_appointments(self, phone: Optional[str] = None) -> List[Appointment]:
        pat = self.get_patient(phone)
        return pat.appointments

    def delete_appointment(self, appt_id: str, phone: Optional[str] = None) -> bool:
        clean = self._normalize_phone(phone)
        with SessionLocal() as session:
            p = session.query(db_models.Patient).filter(
                (db_models.Patient.phone == clean) | (db_models.Patient.id == clean)
            ).first()
            if p:
                db_appt = session.query(db_models.Appointment).filter(
                    db_models.Appointment.id == appt_id,
                    db_models.Appointment.patient_id == p.id
                ).first()
                if db_appt:
                    session.delete(db_appt)
                    session.commit()
                    self.add_activity_log(p.phone, "caretaker", "APPOINTMENT_CANCELLED", f"Appointment {appt_id} cancelled.")
                    return True
        return False

    def add_alert(self, severity: str, title: str, message: str, recipient: str = "caregiver@example.com", phone: Optional[str] = None) -> AlertNotification:
        clean = self._normalize_phone(phone)
        with SessionLocal() as session:
            p = session.query(db_models.Patient).filter(
                (db_models.Patient.phone == clean) | (db_models.Patient.id == clean)
            ).first()
            if not p:
                p = session.query(db_models.Patient).first()
            alert = db_models.Alert(
                id=f"alt_{uuid.uuid4().hex}",
                patient_id=p.id if p else "p_ramesh_72",
                severity=severity,
                title=title,
                message=message,
                recipient_email=recipient,
                status="sent",
                created_at=datetime.now()
            )
            session.add(alert)
            session.commit()
            return AlertNotification(
                id=alert.id,
                patient_id=alert.patient_id,
                timestamp=alert.created_at.strftime("%Y-%m-%d %H:%M"),
                severity=alert.severity,
                title=alert.title,
                message=alert.message,
                recipient_email=alert.recipient_email,
                status=alert.status
            )

    def get_alerts(self, phone: Optional[str] = None) -> List[AlertNotification]:
        clean = self._normalize_phone(phone)
        with SessionLocal() as session:
            p = session.query(db_models.Patient).filter(
                (db_models.Patient.phone == clean) | (db_models.Patient.id == clean)
            ).first()
            if not p and settings.DEMO_MODE:
                p = session.query(db_models.Patient).filter(db_models.Patient.phone == "9849012345").first()
            if p:
                alts = session.query(db_models.Alert).filter(
                    db_models.Alert.patient_id == p.id
                ).order_by(db_models.Alert.created_at.desc()).all()
                return [
                    AlertNotification(
                        id=a.id,
                        patient_id=a.patient_id,
                        timestamp=a.created_at.strftime("%Y-%m-%d %H:%M"),
                        severity=a.severity,
                        title=a.title,
                        message=a.message,
                        recipient_email=a.recipient_email,
                        status=a.status
                    ) for a in alts
                ]
            return []

db = MultiUserDB()
