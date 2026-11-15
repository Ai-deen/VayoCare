from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db, SessionLocal
from app.db import models as db_models
from app.database import db
from app.models import Patient, Medication
from app.services.auth_service import get_current_user, require_current_user
from app.services.email_service import email_engine
from app.services.gemini_service import gemini_service

router = APIRouter(prefix="/api/caregiver", tags=["Caregiver Circle Management"])

class LinkSeniorRequest(BaseModel):
    senior_phone: str
    relationship: Optional[str] = "Family Member"
    caregiver_phone: Optional[str] = None

class ProposeMedicationRequest(BaseModel):
    senior_phone: str
    brand_name: str
    senior_label: str
    salt_composition: Optional[str] = ""
    dosage: Optional[str] = "1 tablet"
    timing_anchor: Optional[str] = "breakfast"
    timing_relation: Optional[str] = "after_food"
    remaining_pills: Optional[int] = 10
    purpose: Optional[str] = "General Health"

class VoiceNoteClassifyRequest(BaseModel):
    caregiver_name: str
    message_text: str
    senior_phone: str

@router.post("/link")
def link_senior(
    req: LinkSeniorRequest,
    current_user: Optional[db_models.User] = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Caregiver requests link to a senior patient.
    Requires Senior confirmation or sets status to approved.
    """
    clean_senior_phone = "".join(c for c in req.senior_phone if c.isdigit())
    if not clean_senior_phone:
        raise HTTPException(status_code=400, detail="Valid senior phone number required.")

    # Find caregiver user
    cg_user = current_user if isinstance(current_user, db_models.User) else None
    if not cg_user and req.caregiver_phone:
        clean_cg_phone = "".join(c for c in req.caregiver_phone if c.isdigit())
        cg_user = session.query(db_models.User).filter(db_models.User.phone == clean_cg_phone).first()

    if not cg_user:
        raise HTTPException(status_code=401, detail="Caregiver identification required.")

    # Find or create senior patient
    senior_patient = session.query(db_models.Patient).filter(db_models.Patient.phone == clean_senior_phone).first()
    if not senior_patient:
        senior_patient = db_models.Patient(
            phone=clean_senior_phone,
            name="Senior Parent",
            age=70,
            gender="Not Specified"
        )
        session.add(senior_patient)
        session.flush()

    # Check existing link
    existing_link = session.query(db_models.CaregiverLink).filter(
        db_models.CaregiverLink.caregiver_user_id == cg_user.id,
        db_models.CaregiverLink.patient_id == senior_patient.id
    ).first()

    if existing_link:
        existing_link.status = "approved"
        session.commit()
        return {
            "status": "success",
            "message": f"Already linked to senior {senior_patient.name} ({senior_patient.phone}).",
            "link_id": existing_link.id
        }

    new_link = db_models.CaregiverLink(
        caregiver_user_id=cg_user.id,
        patient_id=senior_patient.id,
        relationship_type=req.relationship or "Family Member",
        status="approved"
    )
    session.add(new_link)

    # Activity log
    act = db_models.ActivityLog(
        patient_id=senior_patient.id,
        actor_role="caregiver",
        action="CAREGIVER_LINKED",
        details=f"Caregiver {cg_user.name} linked with relationship '{req.relationship}'."
    )
    session.add(act)
    session.commit()

    return {
        "status": "success",
        "message": f"Successfully linked to {senior_patient.name}!",
        "link_id": new_link.id,
        "senior": {
            "id": senior_patient.id,
            "name": senior_patient.name,
            "phone": senior_patient.phone
        }
    }

@router.get("/seniors")
def list_linked_seniors(
    caregiver_phone: Optional[str] = Query(None),
    current_user: Optional[db_models.User] = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """Lists all seniors linked to this caregiver."""
    cg_user = current_user if isinstance(current_user, db_models.User) else None
    if not cg_user and caregiver_phone:
        clean = "".join(c for c in caregiver_phone if c.isdigit())
        cg_user = session.query(db_models.User).filter(db_models.User.phone == clean).first()

    if not cg_user:
        # If demo mode, return Ramesh Rao for demo caregiver
        if db.active_phone == "9849012345":
            p = db.get_patient("9849012345")
            return [{
                "id": p.id,
                "name": p.name,
                "phone": p.phone,
                "age": p.age,
                "gender": p.gender,
                "relationship": "Parent"
            }]
        return []

    links = session.query(db_models.CaregiverLink).filter(
        db_models.CaregiverLink.caregiver_user_id == cg_user.id,
        db_models.CaregiverLink.status == "approved"
    ).all()

    results = []
    for l in links:
        pat = l.patient
        if pat:
            results.append({
                "id": pat.id,
                "name": pat.name,
                "phone": pat.phone,
                "age": pat.age,
                "gender": pat.gender,
                "relationship": l.relationship_type,
                "can_manage_meds": l.can_manage_meds
            })
    return results

@router.delete("/unlink/{link_id_or_patient_id}")
def unlink_senior(
    link_id_or_patient_id: str,
    caregiver_phone: Optional[str] = Query(None),
    current_user: Optional[db_models.User] = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """Unlinks a senior from this caregiver."""
    link = session.query(db_models.CaregiverLink).filter(
        (db_models.CaregiverLink.id == link_id_or_patient_id) |
        (db_models.CaregiverLink.patient_id == link_id_or_patient_id)
    ).first()

    if not link:
        raise HTTPException(status_code=404, detail="Caregiver link record not found.")

    session.delete(link)
    session.commit()
    return {"status": "success", "message": "Senior unlinked successfully."}

@router.post("/propose-medication")
def propose_medication(req: ProposeMedicationRequest):
    """
    Caregiver proposes a medicine. Stays in 'pending_approval' until senior approves it.
    """
    clean_phone = "".join(c for c in req.senior_phone if c.isdigit())
    med = Medication(
        id=f"m_{abs(hash(req.brand_name + clean_phone)) % 1000000}",
        brand_name=req.brand_name,
        senior_label=req.senior_label,
        salt_composition=req.salt_composition or req.brand_name,
        dosage=req.dosage or "1 tablet",
        timing_anchor=req.timing_anchor or "breakfast",
        timing_relation=req.timing_relation or "after_food",
        remaining_pills=req.remaining_pills or 10,
        purpose=req.purpose or "General",
        approval_status="pending_approval",
        added_by="caretaker"
    )
    saved_med = db.add_medication(med, phone=clean_phone)
    return {
        "status": "success",
        "message": f"Proposal for {req.senior_label} submitted. Awaiting approval from senior.",
        "medication": saved_med
    }

@router.post("/classify-voice-note")
def classify_and_send_voice_note(req: VoiceNoteClassifyRequest):
    """
    Classifies voice note target slot (breakfast, lunch, dinner, bedtime) via Gemini,
    or falls back to text parsing, then stores note for the senior.
    """
    anchor = "breakfast"
    msg_lower = req.message_text.lower()

    if gemini_service.is_available():
        prompt = (
            f"Analyze this caregiver's note to an Indian elderly parent: \"{req.message_text}\"\n"
            "Classify the intended daily meal/routine slot into exactly one of: breakfast, lunch, dinner, bedtime."
        )
        sys_inst = "Output JSON format: {\"anchor\": \"breakfast\" | \"lunch\" | \"dinner\" | \"bedtime\"}"
        res = gemini_service.generate_json_response(prompt, sys_inst)
        if res and "anchor" in res and res["anchor"] in ("breakfast", "lunch", "dinner", "bedtime"):
            anchor = res["anchor"]
    else:
        if any(w in msg_lower for w in ["lunch", "afternoon", "madhyanam", "dopahar"]):
            anchor = "lunch"
        elif any(w in msg_lower for w in ["dinner", "night", "ratri", "shaam", "raat"]):
            anchor = "dinner"
        elif any(w in msg_lower for w in ["bedtime", "sleep", "padukune"]):
            anchor = "bedtime"
        else:
            anchor = "breakfast"

    note = db.add_caregiver_voice_note(
        caregiver_name=req.caregiver_name,
        message=req.message_text,
        anchor=anchor,
        phone=req.senior_phone
    )
    return {
        "status": "success",
        "classified_anchor": anchor,
        "message": f"Voice note anchored to {anchor.capitalize()} for your loved one.",
        "note": note
    }
