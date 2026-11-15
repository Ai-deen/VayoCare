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

class OnboardingChatRequest(BaseModel):
    patient_id: str
    message: str
    step: int = 1  # 1: Routine (wake, breakfast, lunch, dinner), 2: Medicines, 3: Conditions/Allergies
    language: str = "en"

@router.post("/onboarding")
def onboarding_conversation(req: OnboardingChatRequest):
    """
    Conversational onboarding via Gemini or deterministic parser:
    Gently collects routine, medicines, conditions, and allergies.
    Saves structured results directly into database without requiring photos.
    """
    from app.services.gemini_service import gemini_service
    from app.services.routine_service import routine_service
    from app.models import Medication, RoutineSchedule
    from app.db.session import SessionLocal
    from app.db import models as db_models

    patient = db.get_patient(req.patient_id)
    lang = req.language or "en"
    clean_phone = patient.phone

    if req.step == 1:
        # Step 1: Parse Routine
        schedule = routine_service.parse_voice_routine(req.message, lang)
        db.update_routine(schedule, phone=clean_phone)
        
        reply_en = f"Wonderful! I have set your daily anchors: Breakfast at {schedule.breakfast}, Lunch at {schedule.lunch}, and Dinner at {schedule.dinner}. Next, what regular medicines or tablets do you take each day?"
        reply_te = f"చాలా బాగుంది! మీ టిఫిన్ సమయం {schedule.breakfast}, భోజనం {schedule.lunch}, మరియు రాత్రి భోజనం {schedule.dinner} కి సెట్ చేసాము. మీరు రోజూ వేసుకునే మాత్రల పేర్లు చెప్పండి?"
        reply_hi = f"बहुत अच्छा! आपका नाश्ता {schedule.breakfast}, दोपहर का खाना {schedule.lunch}, और रात का खाना {schedule.dinner} तय किया गया है। अब बताइये आप रोज़ कौन-सी दवाइयां लेते हैं?"
        
        chosen_reply = reply_te if lang == "te" else (reply_hi if lang == "hi" else reply_en)
        return {
            "step": 2,
            "next_prompt": "medicines",
            "reply": chosen_reply,
            "saved_routine": schedule
        }

    elif req.step == 2:
        # Step 2: Extract Medicines
        extracted_meds = []
        if gemini_service.is_available():
            prompt = (
                f"Extract daily medications from this patient statement: \"{req.message}\"\n"
                "Return a JSON array of objects with keys: brand_name, senior_label, dosage, timing_anchor (breakfast/lunch/dinner/bedtime), remaining_pills, purpose."
            )
            res = gemini_service.generate_json_response(prompt, "Output JSON array only.")
            if res and isinstance(res, list):
                extracted_meds = res
            elif res and isinstance(res, dict) and "medicines" in res:
                extracted_meds = res["medicines"]

        if not extracted_meds:
            # Deterministic extraction fallback
            lines = req.message.replace(",", "\n").split("\n")
            for idx, line in enumerate(lines):
                line_clean = line.strip()
                if not line_clean:
                    continue
                anchor = "lunch" if "lunch" in line_clean.lower() else ("dinner" if "dinner" in line_clean.lower() else "breakfast")
                extracted_meds.append({
                    "brand_name": line_clean[:30],
                    "senior_label": line_clean[:20] or f"Medicine {idx+1}",
                    "dosage": "1 tablet",
                    "timing_anchor": anchor,
                    "remaining_pills": 15,
                    "purpose": "Daily Health"
                })

        saved_list = []
        for m_data in extracted_meds:
            m_id = f"m_{abs(hash(m_data.get('brand_name', '') + clean_phone)) % 1000000}"
            med = Medication(
                id=m_id,
                brand_name=m_data.get("brand_name", "Prescribed Tablet"),
                senior_label=m_data.get("senior_label", "Daily Medicine"),
                salt_composition=m_data.get("brand_name", "Active Salt"),
                dosage=m_data.get("dosage", "1 tablet"),
                timing_anchor=m_data.get("timing_anchor", "breakfast"),
                remaining_pills=int(m_data.get("remaining_pills", 15)),
                purpose=m_data.get("purpose", "General Health"),
                approval_status="approved",
                added_by="elder"
            )
            db.add_medication(med, phone=clean_phone)
            saved_list.append(med)

        reply_en = f"Got it! I have saved {len(saved_list)} medications for you. Lastly, do you have any chronic conditions (like BP, Diabetes, Heart) or drug allergies?"
        reply_te = f"సరేనండి! మీ కోసం {len(saved_list)} మాత్రలను నమోదు చేసుకున్నాము. చివరగా, మీకు BP, షుగర్ లేదా గుండె సమస్యలు ఉన్నాయా? మందుల అలర్జీలు ఏమైనా ఉన్నాయా?"
        reply_hi = f"समझ गया! आपकी {len(saved_list)} दवाइयां दर्ज कर ली गई हैं। आखिरी सवाल, क्या आपको बीपी, शुगर या कोई एलर्जी है?"

        chosen_reply = reply_te if lang == "te" else (reply_hi if lang == "hi" else reply_en)
        return {
            "step": 3,
            "next_prompt": "conditions_allergies",
            "reply": chosen_reply,
            "saved_medications": saved_list
        }

    else:
        # Step 3: Conditions and Allergies
        conditions = []
        allergies = []
        text_lower = req.message.lower()
        if "bp" in text_lower or "blood pressure" in text_lower or "hypertension" in text_lower:
            conditions.append("High Blood Pressure")
        if "sugar" in text_lower or "diabetes" in text_lower:
            conditions.append("Diabetes")
        if "heart" in text_lower or "cardiac" in text_lower:
            conditions.append("Heart Condition")
        if "penicillin" in text_lower:
            allergies.append("Penicillin")
        if "sulfa" in text_lower:
            allergies.append("Sulfa drugs")
        if not conditions:
            conditions.append(req.message[:50])

        with SessionLocal() as session:
            p_db = session.query(db_models.Patient).filter(db_models.Patient.phone == clean_phone).first()
            if p_db:
                p_db.chronic_conditions = conditions
                p_db.allergies = allergies
                session.commit()

        reply_en = f"Thank you! Your health circle is completely configured and ready. Would you also like to upload a photo of your prescription or medicine strips, or proceed to your dashboard?"
        reply_te = f"ధన్యవాదాలు! మీ ఆరోగ్య ప్రొఫైల్ సిద్ధమైంది. మీరు ప్రిస్క్రిప్షన్ లేదా మాత్రల ఫోటో అప్‌లోడ్ చేయాలనుకుంటున్నారా, లేదా డాష్‌బోర్డ్‌కి వెళ్లాలా?"
        reply_hi = f"धन्यवाद! आपका स्वास्थ्य सर्कल तैयार है। क्या आप प्रिस्क्रिप्शन की फोटो जोड़ना चाहते हैं या सीधे डैशबोर्ड पर जाना चाहते हैं?"

        chosen_reply = reply_te if lang == "te" else (reply_hi if lang == "hi" else reply_en)
        return {
            "step": 4,
            "finished": True,
            "reply": chosen_reply,
            "conditions": conditions,
            "allergies": allergies
        }

