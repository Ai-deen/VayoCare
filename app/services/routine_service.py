import re
from typing import Dict, Any
from app.models import RoutineSchedule
from app.services.gemini_service import gemini_service

class RoutineService:
    @staticmethod
    def parse_voice_routine(transcript: str, language: str = "te") -> RoutineSchedule:
        """Parses senior's conversational description of their daily routine."""
        # Try Gemini first if configured
        if gemini_service.is_available():
            system_prompt = (
                "You are an empathetic Indian healthcare assistant. Extract daily routine times "
                "(wake_up, breakfast, lunch, dinner, bedtime in HH:MM 24-hr format) from the senior's voice statement. "
                "Output JSON with keys: wake_up, breakfast, lunch, dinner, bedtime, notes."
            )
            prompt = f"Senior's voice transcript in language ({language}): '{transcript}'"
            res = gemini_service.generate_json_response(prompt, system_prompt)
            if res and "breakfast" in res:
                return RoutineSchedule(
                    wake_up=res.get("wake_up", "08:00"),
                    breakfast=res.get("breakfast", "09:30"),
                    lunch=res.get("lunch", "13:30"),
                    dinner=res.get("dinner", "20:30"),
                    bedtime=res.get("bedtime", "22:00"),
                    notes=res.get("notes", "Parsed via Gemini AI Voice Assistant")
                )

        # Robust rule-based / regex fallback for offline & test guarantees
        text_lower = transcript.lower()
        wake = "07:30"
        breakfast = "09:00"
        lunch = "13:30"
        dinner = "20:30"
        bedtime = "22:00"

        # Check for wake up numbers
        wake_match = re.search(r'(?:wake|లేస్తాను|उठता|morning)\D*?(\d{1,2})', text_lower)
        if wake_match:
            hr = int(wake_match.group(1))
            wake = f"{hr:02d}:00"

        # Check for breakfast / tiffin numbers
        bf_match = re.search(r'(?:breakfast|tiffin|టిఫిన్|నాశ్తా|नाश्ता)\D*?(\d{1,2})(?::(\d{2}))?', text_lower)
        if bf_match:
            hr = int(bf_match.group(1))
            mn = bf_match.group(2) or "00"
            breakfast = f"{hr:02d}:{mn}"

        # Check for lunch / afternoon numbers
        lunch_match = re.search(r'(?:lunch|భోజనం|खाना|afternoon)\D*?(\d{1,2})(?::(\d{2}))?', text_lower)
        if lunch_match:
            hr = int(lunch_match.group(1))
            if hr < 12:
                hr += 12
            mn = lunch_match.group(2) or "30"
            lunch = f"{hr:02d}:{mn}"

        # Check for dinner / night numbers
        din_match = re.search(r'(?:dinner|రాత్రి|रात)\D*?(\d{1,2})(?::(\d{2}))?', text_lower)
        if din_match:
            hr = int(din_match.group(1))
            if hr < 12:
                hr += 12
            mn = din_match.group(2) or "30"
            dinner = f"{hr:02d}:{mn}"

        return RoutineSchedule(
            wake_up=wake,
            breakfast=breakfast,
            lunch=lunch,
            dinner=dinner,
            bedtime=bedtime,
            notes=f"Voice routine captured ({language}): '{transcript[:60]}...'"
        )

    @staticmethod
    def get_current_anchor_slot(routine: RoutineSchedule, current_time_str: str = None) -> str:
        """Determines whether current window is breakfast, lunch, dinner, or bedtime."""
        if not current_time_str:
            from datetime import datetime
            current_time_str = datetime.now().strftime("%H:%M")
        
        # Simple proximity check
        if current_time_str < "11:30":
            return "breakfast"
        elif current_time_str < "16:00":
            return "lunch"
        elif current_time_str < "21:30":
            return "dinner"
        else:
            return "bedtime"

routine_service = RoutineService()
