from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.models import Medication, DoseLog
from app.database import db

router = APIRouter(prefix="/api/medications", tags=["Medications & Adherence"])

class LogDoseRequest(BaseModel):
    medication_id: str
    status: str  # "taken", "skipped", "pending"
    notes: Optional[str] = ""
    triage: Optional[str] = "none"
    phone: Optional[str] = None

class CreateMedicationRequest(BaseModel):
    name: str
    timing_anchor: Optional[str] = "breakfast"
    dosage: Optional[str] = "1 tablet"
    phone: Optional[str] = None

@router.get("", response_model=List[Medication])
def get_medications(phone: Optional[str] = Query(None)):
    return db.get_medications(phone)

@router.post("", response_model=Medication)
def create_medication(req: CreateMedicationRequest):
    med_id = f"m_{int(db.patients.get(req.phone, db.get_patient()).id)}_{req.timing_anchor}_{len(db.get_medications(req.phone))+1}"
    new_med = Medication(
        id=med_id,
        brand_name=req.name,
        senior_label=req.name,
        senior_label_te=req.name,
        senior_label_hi=req.name,
        salt_composition=req.name,
        dosage=req.dosage or "1 tablet",
        timing_anchor=req.timing_anchor or "breakfast",
        timing_relation="after_food",
        criticality="high" if any(w in req.name.lower() for w in ["bp", "sugar", "heart", "blood", "diabet"]) else "low",
        remaining_pills=30,
        daily_doses=1,
        pill_color="#2563EB"
    )
    return db.add_medication(new_med, phone=req.phone)

@router.get("/logs", response_model=List[DoseLog])
def get_dose_logs(phone: Optional[str] = Query(None)):
    return db.get_today_logs(phone)

@router.post("/log", response_model=DoseLog)
def log_dose(req: LogDoseRequest):
    result = db.log_dose(
        med_id=req.medication_id,
        status=req.status,
        notes=req.notes or "",
        triage=req.triage or "none",
        phone=req.phone
    )
    if not result:
        raise HTTPException(status_code=404, detail="Medication not found")
    return result

@router.get("/adherence-summary")
def get_adherence_summary(phone: Optional[str] = Query(None)):
    logs = db.get_today_logs(phone)
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
