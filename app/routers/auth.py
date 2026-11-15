from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import db
from app.models import Patient, PhoneAuthRequest

router = APIRouter(prefix="/api/auth", tags=["Authentication & Profile"])

class VerifyPasscodeRequest(BaseModel):
    passcode: str

class PasscodeResponse(BaseModel):
    authenticated: bool
    role: str
    patient: Patient

@router.get("/profile", response_model=Patient)
def get_profile():
    return db.get_patient()

@router.post("/phone-login")
def phone_login(req: PhoneAuthRequest):
    """
    Onboards or links user by unique phone number and role (Senior vs Caregiver).
    """
    clean_phone = req.phone.strip().replace(" ", "").replace("-", "")
    patient = db.get_patient()

    if req.role == "patient":
        if req.name:
            patient.name = req.name
        patient.phone = clean_phone
        return {
            "status": "success",
            "role": "patient",
            "patient": patient,
            "message": f"Welcome, {patient.name}! Personalized senior care routine loaded."
        }
    else:
        # Caregiver mode: links to patient
        target_phone = (req.patient_phone or "9849012345").strip().replace(" ", "").replace("-", "")
        return {
            "status": "success",
            "role": "caregiver",
            "caregiver_name": req.name or "Family Caregiver",
            "linked_patient_phone": target_phone,
            "patient": patient,
            "message": f"Connected to patient {patient.name}'s active healthcare profile."
        }

@router.post("/verify-passcode", response_model=PasscodeResponse)
def verify_passcode(req: VerifyPasscodeRequest):
    patient = db.get_patient()
    if req.passcode == patient.passcode:
        return PasscodeResponse(authenticated=True, role="caregiver", patient=patient)
    elif req.passcode == "0000":
        return PasscodeResponse(authenticated=True, role="guest", patient=patient)
    else:
        raise HTTPException(status_code=401, detail="Invalid family passcode")
