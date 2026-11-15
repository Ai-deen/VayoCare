import logging
from datetime import datetime
from typing import Optional
from app.models import Patient, Medication, AlertNotification
from app.database import db

logger = logging.getLogger(__name__)

class AlertService:
    @staticmethod
    def _get_valid_email(patient: Patient) -> str:
        for cg in patient.caregivers:
            if cg.email and "@" in cg.email and not cg.email.endswith("@example.com"):
                return cg.email
        return ""

    @staticmethod
    def send_missed_dose_alert(patient: Patient, medication: Medication, reason: str = "") -> AlertNotification:
        """Sends immediate high-priority alert to caregivers when critical dose is missed."""
        recipient = AlertService._get_valid_email(patient)
        
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
            recipient=recipient,
            phone=patient.phone
        )
        if recipient:
            logger.warning(f"[EMAIL DISPATCHED TO {recipient}]: {title} - {message}")
        else:
            logger.info(f"[IN-APP NOTIFICATION STORED FOR {patient.name}]: {title}")
        return alert

    @staticmethod
    def send_refill_alert(patient: Patient, medication: Medication) -> AlertNotification:
        """Sends low-stock refill alert when remaining pills <= 3."""
        recipient = AlertService._get_valid_email(patient)

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
            recipient=recipient,
            phone=patient.phone
        )
        if recipient:
            logger.warning(f"[EMAIL DISPATCHED TO {recipient}]: {title} - {message}")
        else:
            logger.info(f"[IN-APP NOTIFICATION STORED FOR {patient.name}]: {title}")
        return alert

alert_service = AlertService()
