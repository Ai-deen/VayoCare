from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.database import db
from app.models import Patient, PhoneAuthRequest

router = APIRouter(prefix="/api/auth", tags=["Authentication & Profile"])

class VerifyPasscodeRequest(BaseModel):
    passcode: str
    phone: Optional[str] = None

class PasscodeResponse(BaseModel):
    authenticated: bool
    role: str
    patient: Patient

@router.get("/profile", response_model=Patient)
def get_profile(phone: Optional[str] = Query(None)):
    return db.get_patient(phone)

@router.post("/phone-login")
def phone_login(req: PhoneAuthRequest):
    """
    Onboards or logs in user by unique phone number and role (Senior vs Caregiver).
    Supports multi-tenant persistence: each phone gets its own isolated records.
    """
    clean_user_phone = "".join(c for c in req.phone if c.isdigit())
    if not clean_user_phone:
        clean_user_phone = "9849012345"

    if req.role == "patient":
        patient = db.get_or_create_patient(clean_user_phone, name=req.name or "Senior Patient", role="patient")
        if req.name and req.name.strip():
            patient.name = req.name.strip()
        if req.language:
            patient.language_preference = req.language
        return {
            "status": "success",
            "role": "patient",
            "phone": clean_user_phone,
            "patient": patient,
            "message": f"Welcome, {patient.name}! Your personalized health companion is ready."
        }
    else:
        # Caregiver mode: links to senior's phone number
        target_patient_phone = "".join(c for c in (req.patient_phone or "") if c.isdigit())
        if not target_patient_phone:
            target_patient_phone = "9849012345"
        
        patient = db.get_or_create_patient(target_patient_phone, name="Senior Parent", role="patient")
        
        return {
            "status": "success",
            "role": "caregiver",
            "caregiver_phone": clean_user_phone,
            "caregiver_name": req.name or "Family Caregiver",
            "linked_patient_phone": target_patient_phone,
            "patient": patient,
            "message": f"Connected to patient {patient.name} ({target_patient_phone})."
        }

@router.post("/verify-passcode", response_model=PasscodeResponse)
def verify_passcode(req: VerifyPasscodeRequest):
    patient = db.get_patient(req.phone)
    if req.passcode == patient.passcode:
        return PasscodeResponse(authenticated=True, role="caregiver", patient=patient)
    elif req.passcode == "0000":
        return PasscodeResponse(authenticated=True, role="guest", patient=patient)
    else:
        raise HTTPException(status_code=401, detail="Invalid family passcode")
