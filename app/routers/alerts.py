from typing import List
from fastapi import APIRouter
from pydantic import BaseModel
from app.models import AlertNotification
from app.database import db
from app.services.alert_service import alert_service

router = APIRouter(prefix="/api/alerts", tags=["Caregiver Alerts & Notifications"])

class TriggerAlertRequest(BaseModel):
    severity: str = "critical"
    title: str
    message: str

@router.get("", response_model=List[AlertNotification])
def get_alerts():
    return db.get_alerts()

@router.post("/trigger", response_model=AlertNotification)
def trigger_alert(req: TriggerAlertRequest):
    patient = db.get_patient()
    alert = db.add_alert(
        severity=req.severity,
        title=req.title,
        message=req.message,
        recipient=patient.caregivers[0].email if patient.caregivers else "family@example.com"
    )
    return alert
