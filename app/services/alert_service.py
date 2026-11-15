import logging
from datetime import datetime
from typing import Optional
from app.models import Patient, Medication, AlertNotification
from app.database import db

logger = logging.getLogger(__name__)

class AlertService:
    @staticmethod
    def send_missed_dose_alert(patient: Patient, medication: Medication, reason: str = "") -> AlertNotification:
        """Sends immediate high-priority alert to caregivers when critical dose is missed."""
        primary_caregiver = patient.caregivers[0] if patient.caregivers else None
        recipient = primary_caregiver.email if primary_caregiver else "family@example.com"
        
        title = f"⚠️ Critical Alert: Missed Dose for {patient.name}"
        message = (
            f"Senior {patient.name} (Age {patient.age}) missed or declined critical medication: "
            f"'{medication.brand_name}' ({medication.salt_composition}) scheduled for {medication.timing_anchor}. "
            f"Clinical severity: HIGH. Reason captured: '{reason}'. Please check in with them immediately."
        )

        alert = db.add_alert(
            severity="critical",
            title=title,
            message=message,
            recipient=recipient
        )
        logger.warning(f"[EMAIL DISPATCHED TO {recipient}]: {title} - {message}")
        return alert

    @staticmethod
    def send_refill_alert(patient: Patient, medication: Medication) -> AlertNotification:
        """Sends low-stock refill alert when remaining pills <= 3."""
        primary_caregiver = patient.caregivers[0] if patient.caregivers else None
        recipient = primary_caregiver.email if primary_caregiver else "family@example.com"

        title = f"📦 Refill Runway Alert: {medication.brand_name} running low"
        message = (
            f"Medicine '{medication.brand_name}' ({medication.salt_composition}) has only "
            f"{medication.remaining_pills} doses remaining (less than 3 days supply). "
            f"Please show the Refill Card at your local pharmacy."
        )

        alert = db.add_alert(
            severity="warning",
            title=title,
            message=message,
            recipient=recipient
        )
        logger.info(f"[EMAIL DISPATCHED TO {recipient}]: {title}")
        return alert

    @staticmethod
    def send_doctor_appointment_reminder(patient: Patient, doctor_name: str, appointment_time: str) -> AlertNotification:
        """Proactive reminder for doctor consultation."""
        primary_caregiver = patient.caregivers[0] if patient.caregivers else None
        recipient = primary_caregiver.email if primary_caregiver else "family@example.com"

        title = f"🩺 Appointment Reminder: Consultation with {doctor_name}"
        message = (
            f"Upcoming appointment scheduled for {patient.name} with {doctor_name} at {appointment_time}. "
            f"Ensure to carry the 1-Tap Doctor Emergency QR Pass."
        )

        alert = db.add_alert(
            severity="info",
            title=title,
            message=message,
            recipient=recipient
        )
        return alert

alert_service = AlertService()
