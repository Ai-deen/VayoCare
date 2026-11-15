from app.services.routine_service import routine_service
from app.models import RoutineSchedule

def test_parse_english_routine():
    transcript = "I wake up at 8 in the morning, eat breakfast at 9:30, have lunch at 1:30 and dinner at 8:30"
    schedule = routine_service.parse_voice_routine(transcript, language="en")
    assert schedule.breakfast in ["09:30", "09:00"]
    assert schedule.lunch == "13:30"
    assert schedule.dinner == "20:30"

def test_parse_telugu_routine():
    transcript = "ఉదయం 7 గంటలకు లేస్తాను, టిఫిన్ 9 గంటలకు తింటాను, మధ్యాహ్నం భోజనం ఒంటిగంటకు, రాత్రి భోజనం 8:30"
    schedule = routine_service.parse_voice_routine(transcript, language="te")
    assert schedule.breakfast == "09:00"
    assert schedule.dinner == "20:30"

def test_anchor_slot_calculation():
    slot_morning = routine_service.get_current_anchor_slot(RoutineSchedule(), "09:15")
    slot_afternoon = routine_service.get_current_anchor_slot(RoutineSchedule(), "14:00")
    slot_night = routine_service.get_current_anchor_slot(RoutineSchedule(), "20:45")
    
    assert slot_morning == "breakfast"
    assert slot_afternoon == "lunch"
    assert slot_night == "dinner"
