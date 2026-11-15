import re
from typing import Tuple, List, Optional
from app.models import CompanionChatResponse, Medication, Patient
from app.database import db
from app.services.gemini_service import gemini_service
from app.services.alert_service import alert_service

class TriageService:
    @staticmethod
    def process_companion_input(
        patient: Patient,
        user_speech: str,
        language: str = "te",
        anchor: str = "breakfast"
    ) -> CompanionChatResponse:
        """
        Processes voice/text input from the senior with off-topic redirection,
        clinical severity classification, and native-tongue response generation.
        """
        # Find active medication for this anchor
        pending_meds = [
            m for m in db.get_medications()
            if m.timing_anchor == anchor
        ]
        target_med: Optional[Medication] = pending_meds[0] if pending_meds else None
        target_med_id = target_med.id if target_med else None
        target_med_name = target_med.brand_name if target_med else "Daily Medicine"
        target_criticality = target_med.criticality if target_med else "medium"
        target_med_image = target_med.image_url if target_med else None

        # Check for Gemini dynamic response
        if gemini_service.is_available():
            system_instruction = (
                "You are 'ArogyaMitra', an empathetic AI health companion for an elderly Indian parent. "
                "The senior speaks in Telugu, Hindi, or Indian English. "
                "Task 1: If they talk about personal things (shopping, visiting relatives, gossip, weather), "
                "politely acknowledge it in 1 short warm sentence, but immediately redirect them back to asking "
                f"if they took their {target_med_name} ({target_criticality} criticality). "
                "Task 2: Detect if they say they took the medicine, skipped it, or reported symptoms (headache, dizziness, pain). "
                "Return JSON with: "
                "reply_text (written in chosen language script), "
                "spoken_text (warm conversational phonetic text for speech synthesis), "
                "redirected_offtopic (boolean), "
                "detected_symptoms (array of strings), "
                "action_taken ('dose_marked_taken', 'dose_snoozed', 'caregiver_alerted', 'clarification_needed')"
            )
            prompt = (
                f"Language: {language}\n"
                f"Anchor: {anchor}\n"
                f"Medicine: {target_med_name} (Criticality: {target_criticality})\n"
                f"Senior's Speech: '{user_speech}'"
            )
            res = gemini_service.generate_json_response(prompt, system_instruction)
            if res and "reply_text" in res:
                action = res.get("action_taken", "clarification_needed")
                if action == "dose_marked_taken" and target_med_id:
                    db.log_dose(target_med_id, "taken", notes="Confirmed via Voice Companion", triage="none")
                elif action == "caregiver_alerted" and target_med:
                    db.log_dose(target_med_id, "skipped", notes="Senior declined/unwell", triage="escalated")
                    alert_service.send_missed_dose_alert(patient, target_med, reason=user_speech)
                elif action == "dose_snoozed" and target_med_id:
                    db.log_dose(target_med_id, "pending", notes="Snoozed low-priority dose", triage="snoozed")

                return CompanionChatResponse(
                    reply_text=res["reply_text"],
                    spoken_text=res.get("spoken_text", res["reply_text"]),
                    language=language,
                    redirected_offtopic=res.get("redirected_offtopic", False),
                    detected_symptoms=res.get("detected_symptoms", []),
                    action_taken=action,
                    target_medication_id=target_med_id,
                    target_medication_name=target_med_name,
                    target_medication_image=target_med_image,
                    criticality=target_criticality
                )

        # Robust, high-fidelity native rule-based NLP fallback
        text_lower = user_speech.lower()
        redirected = False
        action = "clarification_needed"
        symptoms = []

        # 1. Symptom detection
        if any(w in text_lower for w in ["headache", "నొప్పి", "తల", "బాధ", "दर्द", "सर दर्द", "dizzy", "కళ్లు తిరుగుతున్నాయి", "चक्कर", "fever", "జ్వరం", "बुखार"]):
            symptoms.append("Senior reported feeling unwell / headache or dizziness")

        # 2. Off-topic detection (rambling about shopping, clothes, market, relatives)
        offtopic_keywords = [
            "cloth", "outside", "bought", "market", "friend", "shopping",
            "బట్టలు", "బయటకు", "స్నేహితుడు", "కొన్నాను", "షాపూర్", "బాట",
            "कपड़े", "बाजार", "दोस्त", "खरीदा", "घूमने"
        ]
        if any(w in text_lower for w in offtopic_keywords):
            redirected = True

        # 3. Medicine confirmation check
        taken_keywords = [
            "taken", "took", "had it", "yes", "done", "వేసుకున్నాను", "వేసుకున్నా", "తిన్నాను", "తీసుకున్నాను",
            "హా", "అయిపోయింది", "లే లియా", "खा लिया", "हाँ", "हो गया"
        ]
        skipped_keywords = [
            "no", "didn't", "not taken", "forgot", "don't want", "skip",
            "లేదు", "వేసుకోలేదు", "తినలేదు", "వద్దు", "తర్వాత",
            "नहीं", "नहीं लिया", "मन नहीं", "बाद में"
        ]

        is_taken = any(w in text_lower for w in taken_keywords)
        is_skipped = any(w in text_lower for w in skipped_keywords)

        if is_taken and not is_skipped:
            action = "dose_marked_taken"
            if target_med_id:
                db.log_dose(target_med_id, "taken", notes="Voice confirmed taken", triage="none")
            
            if language == "te":
                reply = f"చాలా మంచిది అండీ! మీ {target_med_name} వేసుకున్నారు. నేను డైలీ లాగ్‌లో రికార్డ్ చేశాను. శుభ దినం!"
            elif language == "hi":
                reply = f"बहुत अच्छा जी! आपने {target_med_name} ले ली है। मैंने इसे लॉग कर दिया है। आपका दिन शुभ हो!"
            else:
                reply = f"Excellent! You have taken {target_med_name}. I have marked it in your daily health record."

        elif is_skipped:
            if target_criticality == "high":
                action = "caregiver_alerted"
                if target_med_id:
                    db.log_dose(target_med_id, "skipped", notes="Crucial dose skipped", triage="escalated")
                if target_med:
                    alert_service.send_missed_dose_alert(patient, target_med, reason=user_speech)
                
                if language == "te":
                    reply = f"అయ్యో, {target_med_name} మీ రక్తపోటు/షుగర్‌కి చాలా ముఖ్యం అండీ. దయచేసి నీటితో వేసుకోండి. నేను మీ కేర్‌టేకర్‌కి కూడా సమాచారం పంపాను."
                elif language == "hi":
                    reply = f"कृपया ध्यान दें, {target_med_name} आपकी सेहत के लिए बहुत ज़रूरी दवा है। इसे छोड़ना ठीक नहीं। मैंने परिवार को भी सूचित किया है।"
                else:
                    reply = f"Please note: {target_med_name} is a high-priority medication for your vitals. Please take it with water. I have notified your caregiver."
            else:
                action = "dose_snoozed"
                if target_med_id:
                    db.log_dose(target_med_id, "pending", notes="Vitamin dose snoozed", triage="snoozed")
                
                if language == "te":
                    reply = f"పర్వాలేదు అండీ, ఇది సప్లిమెంట్ మాత్రమే. మీకు వీలైనప్పుడు మధ్యాహ్నం వేసుకోండి."
                elif language == "hi":
                    reply = f"कोई बात नहीं, यह केवल सप्लीमेंट है। जब आपको सहज लगे तब ले लीजिएगा।"
                else:
                    reply = f"No worries, {target_med_name} is a supplement. You can take it comfortably a bit later."

        else:
            # Handle off-topic redirect or prompt
            if redirected:
                if language == "te":
                    reply = f"బయటకు వెళ్లి రావడం సంతోషకరం అండీ! కానీ మీ ఆరోగ్యం ముఖ్యం కదా, మీరు మీ {target_med_name} tablet వేసుకున్నారా?"
                elif language == "hi":
                    reply = f"बाहर जाना अच्छा रहा, जानकर खुशी हुई! लेकिन सेहत पहले है—क्या आपने {target_med_name} गोली ली?"
                else:
                    reply = f"Glad you had a pleasant outing! However, your health comes first: did you take your morning {target_med_name} tablet yet?"
            else:
                if language == "te":
                    reply = f"నమస్కారం అండీ! మీ {target_med_name} tablet వేసుకున్నారా? 'హా వేసుకున్నాను' లేదా 'లేదు' అని చెప్పండి."
                elif language == "hi":
                    reply = f"नमस्ते जी! क्या आपने {target_med_name} गोली ली? कृपया 'हाँ ली' या 'नहीं ली' कहें।"
                else:
                    reply = f"Hello! Have you taken your {target_med_name} tablet? You can say 'Yes, taken' or 'Not yet'."

        return CompanionChatResponse(
            reply_text=reply,
            spoken_text=reply,
            language=language,
            redirected_offtopic=redirected,
            detected_symptoms=symptoms,
            action_taken=action,
            target_medication_id=target_med_id,
            target_medication_name=target_med_name,
            target_medication_image=target_med_image,
            criticality=target_criticality
        )

triage_service = TriageService()
