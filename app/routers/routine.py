from fastapi import APIRouter
from app.models import RoutineSchedule, RoutineVoiceParseRequest
from app.database import db
from app.services.routine_service import routine_service

router = APIRouter(prefix="/api/routine", tags=["Routine-Anchored Schedule"])

@router.get("", response_model=RoutineSchedule)
def get_routine():
    return db.get_patient().routine

@router.post("", response_model=RoutineSchedule)
def update_routine(schedule: RoutineSchedule):
    return db.update_routine(schedule)

@router.post("/parse-voice", response_model=RoutineSchedule)
def parse_voice_routine(req: RoutineVoiceParseRequest):
    new_schedule = routine_service.parse_voice_routine(req.voice_transcript, req.language)
    return db.update_routine(new_schedule)

@router.get("/current-anchor")
def get_current_anchor():
    patient = db.get_patient()
    slot = routine_service.get_current_anchor_slot(patient.routine)
    return {
        "current_anchor": slot,
        "routine": patient.routine
    }
