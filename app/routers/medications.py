from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models import Medication, DoseLog
from app.database import db

router = APIRouter(prefix="/api/medications", tags=["Medications & Adherence"])

class LogDoseRequest(BaseModel):
    medication_id: str
    status: str  # "taken", "skipped", "pending"
    notes: Optional[str] = ""
    triage: Optional[str] = "none"

@router.get("", response_model=List[Medication])
def get_medications():
    return db.get_medications()

@router.get("/logs", response_model=List[DoseLog])
def get_dose_logs():
    return db.get_today_logs()

@router.post("/log", response_model=DoseLog)
def log_dose(req: LogDoseRequest):
    result = db.log_dose(
        med_id=req.medication_id,
        status=req.status,
        notes=req.notes or "",
        triage=req.triage or "none"
    )
    if not result:
        raise HTTPException(status_code=404, detail="Medication not found")
    return result

@router.get("/adherence-summary")
def get_adherence_summary():
    logs = db.get_today_logs()
    total = len(logs)
    taken = sum(1 for l in logs if l.status == "taken")
    skipped = sum(1 for l in logs if l.status == "skipped")
    pending = sum(1 for l in logs if l.status == "pending")
    percentage = int((taken / total) * 100) if total > 0 else 100
    
    return {
        "total_scheduled": total,
        "taken": taken,
        "skipped": skipped,
        "pending": pending,
        "adherence_rate_pct": percentage,
        "status_color": "green" if percentage >= 80 else ("amber" if percentage >= 50 else "red")
    }
