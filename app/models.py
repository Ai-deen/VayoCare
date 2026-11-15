from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class RoutineSchedule(BaseModel):
    wake_up: str = "08:00"
    breakfast: str = "09:30"
    lunch: str = "13:30"
    dinner: str = "20:30"
    bedtime: str = "22:00"
    notes: Optional[str] = "Routine anchored to daily meals"

class Caregiver(BaseModel):
    id: str
    name: str
    relationship: str
    phone: str
    email: str
    role: str = "caregiver"  # "caregiver" or "family"
    notify_missed_dose: bool = True
    notify_low_stock: bool = True

class DoctorContact(BaseModel):
    name: str
    specialty: str
    hospital: str
    phone: str

class Medication(BaseModel):
    id: str
    brand_name: str
    senior_label: str = "Daily Tablet"
    senior_label_te: str = "రోజువారీ మాత్ర"
    senior_label_hi: str = "दैनिक गोली"
    salt_composition: str
    dosage: str
    timing_anchor: str  # "breakfast", "lunch", "dinner", "bedtime"
    timing_relation: str = "after_food"
    criticality: str = "high"  # "high", "medium", "low"
    remaining_pills: int = 20
    daily_doses: int = 1
    pill_color: str = "#2563EB"
    image_url: Optional[str] = None
    purpose: str = "General"
    approval_status: str = "approved"  # "approved" or "pending_approval"
    added_by: str = "elder"  # "elder" or "caretaker"

class DoseLog(BaseModel):
    id: str
    medication_id: str
    medication_name: str
    senior_label: str = "Daily Tablet"
    patient_id: str
    timing_anchor: str
    status: str = "pending"  # "taken", "skipped", "pending"
    logged_at: Optional[str] = None
    feedback_notes: Optional[str] = None
    triage_action: str = "none"

class CaregiverVoiceNote(BaseModel):
    id: str
    caregiver_name: str
    message_text: str
    audio_url: Optional[str] = None
    created_at: str
    assigned_anchor: str = "breakfast"

class Appointment(BaseModel):
    id: str
    doctor_name: str
    specialty: str
    hospital: str
    phone: Optional[str] = ""
    date: str  # "YYYY-MM-DD"
    time: str  # "HH:MM"
    notes: Optional[str] = ""
    status: str = "scheduled"  # "scheduled", "completed", "cancelled"

class ActivityLog(BaseModel):
    id: str
    timestamp: str
    actor_role: str  # "elder", "caretaker", "family", "system"
    action: str
    details: str

class Patient(BaseModel):
    id: str
    name: str
    age: int
    gender: str
    phone: str
    passcode: str = ""
    language_preference: str = "en"
    chronic_conditions: List[str] = []
    allergies: List[str] = []
    routine: RoutineSchedule = Field(default_factory=RoutineSchedule)
    caregivers: List[Caregiver] = []
    doctor: Optional[DoctorContact] = None
    voice_notes: List[CaregiverVoiceNote] = []
    appointments: List[Appointment] = []
    activity_logs: List[ActivityLog] = []

class PhoneAuthRequest(BaseModel):
    role: str  # "patient", "caregiver", "family"
    name: str
    phone: str
    patient_phone: Optional[str] = None
    language: Optional[str] = "en"

class CompanionChatRequest(BaseModel):
    patient_id: str
    speech_text: str
    language: str = "en"
    current_anchor: Optional[str] = "breakfast"

class CompanionChatResponse(BaseModel):
    reply_text: str
    spoken_text: str
    language: str
    redirected_offtopic: bool
    detected_symptoms: List[str] = []
    action_taken: str
    target_medication_id: Optional[str] = None
    target_medication_name: Optional[str] = None
    target_senior_label: Optional[str] = None
    criticality: Optional[str] = None

class RoutineVoiceParseRequest(BaseModel):
    patient_id: str
    voice_transcript: str
    language: str = "en"

class AuditDiscrepancy(BaseModel):
    issue_type: str
    medicine_name: str
    details: str
    severity: str

class RefillRunwayItem(BaseModel):
    brand_name: str
    senior_label: str
    salt: str
    remaining_pills: int
    days_left: int
    urgency: str

class PrescriptionAuditResponse(BaseModel):
    matched_medicines: List[Dict[str, Any]] = []
    discrepancies: List[AuditDiscrepancy] = []
    refill_runway: List[RefillRunwayItem] = []
    next_checkup_recommendation: Optional[str] = "Cardiology & Diabetology follow-up recommended in 21 days."
    confidence_score: float = 0.94
    match_score: int = 90
    summary: str = "Prescription reconciliation complete"
    verified_salts: List[str] = []

class EmergencyViewData(BaseModel):
    patient_name: str
    age: int
    gender: str
    chronic_conditions: List[str]
    allergies: List[str]
    primary_doctor: Optional[DoctorContact]
    emergency_contacts: List[Caregiver]
    active_medications_and_salts: List[Dict[str, Any]]
    today_dose_history: List[DoseLog]
    pin_verified: bool
    valid_until: str

class AlertNotification(BaseModel):
    id: str
    patient_id: str
    timestamp: str
    severity: str  # "info", "warning", "critical"
    title: str
    message: str
    recipient_email: str
    status: str
