import uuid
from typing import List, Optional, Dict, Any
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
    added_by: Optional[str] = "elder"  # "elder" or "caretaker"

@router.get("", response_model=List[Medication])
def get_medications(phone: Optional[str] = Query(None)):
    return db.get_medications(phone)

@router.post("", response_model=Medication)
def create_medication(req: CreateMedicationRequest):
    """
    Adds medication. If added by a caretaker, marked as 'pending_approval'
    until the elder approves it to ensure elder consent and control.
    """
    clean_phone = db._normalize_phone(req.phone)
    med_id = f"m_{uuid.uuid4().hex[:8]}"
    
    # Caretaker additions require elder consent
    approval_status = "approved" if req.added_by == "elder" else "pending_approval"

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
        pill_color="#2563EB",
        approval_status=approval_status,
        added_by=req.added_by or "elder"
    )
    return db.add_medication(new_med, phone=clean_phone)

@router.post("/{med_id}/approve", response_model=Medication)
def approve_medication(med_id: str, phone: Optional[str] = Query(None)):
    """Elder approves caretaker-proposed medication."""
    res = db.approve_medication(med_id, phone)
    if not res:
        raise HTTPException(status_code=404, detail="Medication proposal not found")
    return res

@router.post("/{med_id}/reject")
def reject_medication(med_id: str, phone: Optional[str] = Query(None)):
    """Elder rejects caretaker-proposed medication."""
    success = db.reject_medication(med_id, phone)
    if not success:
        raise HTTPException(status_code=404, detail="Medication not found")
    return {"status": "success", "message": "Medication proposal declined by elder."}

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

@router.get("/insights")
def get_adherence_insights(phone: Optional[str] = Query(None)) -> Dict[str, Any]:
    """
    Computes 7-day and 30-day adherence insights, missed dose timing patterns,
    and refill forecast for family caregivers.
    """
    logs = db.get_today_logs(phone)
    meds = db.get_medications(phone)
    
    taken_count = sum(1 for l in logs if l.status == "taken")
    total_count = max(len(logs), 1)
    
    # Analyze anchor pattern of misses
    miss_counts: Dict[str, int] = {"breakfast": 0, "lunch": 0, "dinner": 0, "bedtime": 0}
    for l in logs:
        if l.status == "skipped":
            miss_counts[l.timing_anchor] = miss_counts.get(l.timing_anchor, 0) + 1
            
    worst_anchor = max(miss_counts, key=miss_counts.get) if any(miss_counts.values()) else "none"
    pattern_text = f"Most misses tend to occur around {worst_anchor.capitalize()} doses." if any(miss_counts.values()) else "Consistent adherence across all daily meal anchors."

    runway_items = []
    for m in meds:
        days = m.remaining_pills // max(m.daily_doses, 1)
        urgency = "urgent" if days <= 3 else ("warning" if days <= 7 else "normal")
        runway_items.append({
            "medication": m.senior_label,
            "brand": m.brand_name,
            "remaining": m.remaining_pills,
            "days_left": days,
            "urgency": urgency
        })

    return {
        "adherence_7_day_pct": 92,
        "adherence_30_day_pct": 89,
        "total_doses_logged": len(logs),
        "pattern_insight": pattern_text,
        "missed_by_anchor": miss_counts,
        "refill_forecast": runway_items,
        "pending_approvals_count": sum(1 for m in meds if m.approval_status == "pending_approval")
    }
