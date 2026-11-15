from datetime import datetime
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional
from app.models import CompanionChatRequest, CompanionChatResponse
from app.database import db
from app.services.triage_service import triage_service

router = APIRouter(prefix="/api/companion", tags=["Voice Health Companion"])

class AddVoiceNoteRequest(BaseModel):
    caregiver_name: str
    message_text: str
    assigned_anchor: Optional[str] = "breakfast"
    patient_phone: Optional[str] = None

def get_current_time_anchor() -> str:
    now = datetime.now()
    cur_time = now.strftime("%H:%M")
    if cur_time < "11:30":
        return "breakfast"
    elif cur_time < "16:00":
        return "lunch"
    elif cur_time < "21:30":
        return "dinner"
    else:
        return "bedtime"

@router.post("/chat", response_model=CompanionChatResponse)
def companion_chat(req: CompanionChatRequest):
    patient = db.get_patient(req.patient_id)
    anchor = req.current_anchor or get_current_time_anchor()
    response = triage_service.process_companion_input(
        patient=patient,
        user_speech=req.speech_text,
        language=req.language,
        anchor=anchor
    )
    return response

@router.get("/greeting")
def get_greeting(
    language: str = "en",
    anchor: Optional[str] = None,
    phone: Optional[str] = Query(None)
):
    """Returns warm, time-appropriate greeting (Breakfast, Lunch, Dinner)."""
    patient = db.get_patient(phone)
    current_slot = anchor or get_current_time_anchor()
    
    # Find medicines specifically scheduled for this slot
    meds = [m for m in db.get_medications(phone) if m.timing_anchor == current_slot]
    
    if meds:
        m = meds[0]
        friendly_name = m.senior_label_te if language == "te" else (m.senior_label_hi if language == "hi" else m.senior_label)
    else:
        # Fallback names per anchor
        if current_slot == "lunch":
            friendly_name = "మధ్యాహ్నం భోజనం మాత్రలు" if language == "te" else ("दोपहर की दवा" if language == "hi" else "Afternoon Medicine")
        elif current_slot == "dinner":
            friendly_name = "రాత్రి భోజనం మాత్రలు" if language == "te" else ("रात की दवा" if language == "hi" else "Night Medicine")
        else:
            friendly_name = "ఉదయం BP మాత్ర" if language == "te" else ("सुबह की बीपी की दवा" if language == "hi" else "Morning BP Tablet")

    # Check for actual caregiver notes for this specific patient
    notes = [n for n in patient.voice_notes if n.assigned_anchor == current_slot]
    caregiver_msg = notes[0].message_text if notes else None

    # Meal labels
    if current_slot == "lunch":
        meal_en, meal_te, meal_hi = "lunch", "మధ్యాహ్నం భోజనం", "दोपहर का खाना"
        time_salutation = "Good afternoon"
    elif current_slot == "dinner":
        meal_en, meal_te, meal_hi = "dinner", "రాత్రి భోజనం", "रात का खाना"
        time_salutation = "Good evening"
    else:
        meal_en, meal_te, meal_hi = "breakfast", "ఉదయం టిఫిన్", "सुबह का नाश्ता"
        time_salutation = "Good morning"

    if language == "te":
        if caregiver_msg:
            text = f"నమస్కారం {patient.name} గారు! కుటుంబ సందేశం: \"{caregiver_msg}\" మీరు {friendly_name} వేసుకున్నారా?"
        else:
            text = f"నమస్కారం {patient.name} గారు! {meal_te} అయిపోయిందా? మీ {friendly_name} వేసుకున్నారా?"
        spoken = text
    elif language == "hi":
        if caregiver_msg:
            text = f"नमस्ते {patient.name} जी! परिवार से संदेश: \"{caregiver_msg}\" क्या आपने {friendly_name} ली?"
        else:
            text = f"नमस्ते {patient.name} जी! क्या आपका {meal_hi} हो गया? क्या आपने {friendly_name} ले ली?"
        spoken = text
    else:
        if caregiver_msg:
            text = f"{time_salutation} {patient.name}! Family note: \"{caregiver_msg}\" Have you taken your {friendly_name}?"
        else:
            text = f"{time_salutation} {patient.name}! Have you finished your {meal_en}? Did you take your {friendly_name}?"
        spoken = text

    return {
        "text": text,
        "spoken": spoken,
        "language": language,
        "current_anchor": current_slot,
        "active_medicine": friendly_name,
        "caregiver_note": caregiver_msg
    }

@router.post("/caregiver-note")
def add_caregiver_note(req: AddVoiceNoteRequest):
    note = db.add_caregiver_voice_note(
        caregiver_name=req.caregiver_name,
        message=req.message_text,
        anchor=req.assigned_anchor or "breakfast",
        phone=req.patient_phone
    )
    return {
        "status": "success",
        "message": f"Personalized voice note from {req.caregiver_name} saved for {req.assigned_anchor}.",
        "note": note
    }
