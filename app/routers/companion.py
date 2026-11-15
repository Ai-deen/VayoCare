from fastapi import APIRouter
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

@router.post("/chat", response_model=CompanionChatResponse)
def companion_chat(req: CompanionChatRequest):
    patient = db.get_patient()
    anchor = req.current_anchor or "breakfast"
    response = triage_service.process_companion_input(
        patient=patient,
        user_speech=req.speech_text,
        language=req.language,
        anchor=anchor
    )
    return response

@router.get("/greeting")
def get_greeting(language: str = "te", anchor: str = "breakfast"):
    """Returns warm greeting with loving caregiver note if present."""
    patient = db.get_patient()
    meds = [m for m in db.get_medications() if m.timing_anchor == anchor]
    
    # Senior friendly names
    if meds:
        m = meds[0]
        friendly_name = m.senior_label_te if language == "te" else (m.senior_label_hi if language == "hi" else m.senior_label)
    else:
        friendly_name = "మాత్రలు / Medicines"

    # Check for loving caregiver note
    notes = [n for n in patient.voice_notes if n.assigned_anchor == anchor]
    caregiver_msg = notes[0].message_text if notes else None

    if language == "te":
        if caregiver_msg:
            text = f"నమస్కారం {patient.name} గారు! మీ అబ్బాయి నుంచి సందేశం: \"{caregiver_msg}\" మీరు మాత్ర వేసుకున్నారా?"
            spoken = f"నమస్కారం అండీ! మీ అబ్బాయి గుర్తుచేశారు: మీరు టిఫిన్ తిని {friendly_name} వేసుకున్నారా?"
        else:
            text = f"నమస్కారం అండీ! టిఫిన్ అయిపోయిందా? మీ {friendly_name} వేసుకున్నారా?"
            spoken = text
    elif language == "hi":
        if caregiver_msg:
            text = f"नमस्ते {patient.name} जी! परिवार से संदेश: \"{caregiver_msg}\" क्या आपने दवा ली?"
            spoken = f"नमस्ते जी! क्या आपने नाश्ते के बाद अपनी {friendly_name} ले ली?"
        else:
            text = f"नमस्ते जी! क्या आपका नाश्ता हो गया? अपनी {friendly_name} ली क्या?"
            spoken = text
    else:
        if caregiver_msg:
            text = f"Good morning {patient.name}! Family note: \"{caregiver_msg}\" Have you taken your tablet?"
            spoken = f"Good morning! Have you finished breakfast and taken your {friendly_name}?"
        else:
            text = f"Good morning! Have you finished your breakfast? Did you take your {friendly_name}?"
            spoken = text

    return {
        "text": text,
        "spoken": spoken,
        "language": language,
        "caregiver_note": caregiver_msg
    }

@router.post("/caregiver-note")
def add_caregiver_note(req: AddVoiceNoteRequest):
    note = db.add_caregiver_voice_note(
        caregiver_name=req.caregiver_name,
        message=req.message_text,
        anchor=req.assigned_anchor or "breakfast"
    )
    return {
        "status": "success",
        "message": f"Personalized voice note from {req.caregiver_name} saved for {req.assigned_anchor} reminder.",
        "note": note
    }
