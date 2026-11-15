from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query
from pydantic import BaseModel
from app.models import AlertNotification, ActivityLog
from app.database import db
from app.services.email_service import email_engine

router = APIRouter(prefix="/api/alerts", tags=["Caregiver Alerts & Notifications"])

class TriggerAlertRequest(BaseModel):
    severity: str = "critical"
    title: str
    message: str
    phone: Optional[str] = None

@router.get("", response_model=List[AlertNotification])
def get_alerts(phone: Optional[str] = Query(None)):
    return db.get_alerts(phone)

@router.get("/outbox")
def get_email_outbox(limit: int = 50) -> List[Dict[str, Any]]:
    """Inspects verified outbound email delivery log."""
    return email_engine.get_outbox(limit)

@router.get("/activity-log", response_model=List[ActivityLog])
def get_activity_log(phone: Optional[str] = Query(None)):
    """Audits family circle activity: dose logs, medication proposals, logins, approvals."""
    return db.get_activity_logs(phone)

@router.post("/trigger", response_model=AlertNotification)
def trigger_alert(req: TriggerAlertRequest):
    patient = db.get_patient(req.phone)
    target_email = patient.caregivers[0].email if patient.caregivers else f"caregiver_{patient.phone}@example.com"
    
    alert = db.add_alert(
        severity=req.severity,
        title=req.title,
        message=req.message,
        recipient=target_email,
        phone=patient.phone
    )

    # Proactively dispatch via EmailEngine with deduplication
    idem_key = f"alert_trigger_{patient.phone}_{req.title}_{int(datetime.now().timestamp() // 60)}" if "datetime" in globals() else f"alert_{patient.phone}_{req.title}"
    body_html = f"""
    <h3>VayoCare Health Alert</h3>
    <p><strong>Patient:</strong> {patient.name} ({patient.phone})</p>
    <p><strong>Severity:</strong> {req.severity.upper()}</p>
    <p><strong>Notice:</strong> {req.message}</p>
    """
    email_engine.send_email(
        to_email=target_email,
        subject=f"[{req.severity.upper()}] {req.title} - {patient.name}",
        body_html=body_html,
        category="critical_alert",
        idempotency_key=f"alert_{alert.id}"
    )

    return alert
