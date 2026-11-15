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
    senior_label: str = "Daily Tablet"  # Friendly name: "BP Tablet", "Sugar Tablet"
    senior_label_te: str = "రోజువారీ మాత్ర"
    senior_label_hi: str = "दैनिक गोली"
    salt_composition: str
    dosage: str
    timing_anchor: str  # "breakfast", "lunch", "dinner", "bedtime"
    timing_relation: str = "after_food"  # "before_food", "after_food"
    criticality: str = "high"  # "high", "medium", "low"
    remaining_pills: int = 20
    daily_doses: int = 1
    pill_color: str = "#2563EB"
    image_url: Optional[str] = None
    purpose: str = "General"

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

class Patient(BaseModel):
    id: str
    name: str
    age: int
    gender: str
    phone: str
    passcode: str = "4321"
    language_preference: str = "te"  # "te", "hi", "en"
    chronic_conditions: List[str] = []
    allergies: List[str] = []
    routine: RoutineSchedule = Field(default_factory=RoutineSchedule)
    caregivers: List[Caregiver] = []
    doctor: Optional[DoctorContact] = None
    voice_notes: List[CaregiverVoiceNote] = []

class PhoneAuthRequest(BaseModel):
    role: str  # "patient" or "caregiver"
    name: str
    phone: str
    patient_phone: Optional[str] = None  # If caretaker, links to patient's phone
    language: Optional[str] = "te"

class CompanionChatRequest(BaseModel):
    patient_id: str
    speech_text: str
    language: str = "te"
    current_anchor: Optional[str] = "breakfast"

class CompanionChatResponse(BaseModel):
    reply_text: str
    spoken_text: str
    language: str
    redirected_offtopic: bool
    detected_symptoms: List[str] = []
    action_taken: str  # "dose_marked_taken", "dose_snoozed", "caregiver_alerted", "clarification_needed"
    target_medication_id: Optional[str] = None
    target_medication_name: Optional[str] = None
    target_senior_label: Optional[str] = None
    criticality: Optional[str] = None

class RoutineVoiceParseRequest(BaseModel):
    patient_id: str
    voice_transcript: str
    language: str = "te"

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
    image_hint: str

class PrescriptionAuditResponse(BaseModel):
    matched_medicines: List[Dict[str, Any]]
    discrepancies: List[AuditDiscrepancy]
    refill_runway: List[RefillRunwayItem]
    next_checkup_recommendation: Optional[str]
    confidence_score: float

class EmergencyViewData(BaseModel):
    patient_name: str
    age: int
    gender: str
    chronic_conditions: List[str]
    allergies: List[str]
    primary_doctor: Optional[DoctorContact]
    emergency_contacts: List[Caregiver]
    active_medications_and_salts: List[Dict[str, str]]
    today_dose_history: List[DoseLog]
    pin_verified: bool
    valid_until: str

class AlertNotification(BaseModel):
    id: str
    patient_id: str
    timestamp: str
    severity: str
    title: str
    message: str
    recipient_email: str
    status: str = "sent"
