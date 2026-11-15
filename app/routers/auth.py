import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from app.database import db
from app.models import Patient, PhoneAuthRequest, ActivityLog
from app.services.security_service import security_service

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
    Onboards or logs in user by phone number and role (Senior, Caregiver, Family).
    Enforces rate limits and logs auth activity.
    """
    clean_user_phone = "".join(c for c in req.phone if c.isdigit())
    if not clean_user_phone:
        clean_user_phone = "9849012345"

    # Check lockout
    is_locked, remaining_seconds = security_service.is_locked_out(clean_user_phone)
    if is_locked:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account temporarily locked due to 5 consecutive failed attempts. Please retry in {remaining_seconds} seconds."
        )

    if req.role == "patient" or req.role == "elder":
        patient = db.get_or_create_patient(clean_user_phone, name=req.name or "Senior Patient", role="patient")
        if req.name and req.name.strip():
            patient.name = req.name.strip()
        if req.language:
            patient.language_preference = req.language
        
        # Log activity
        db.add_activity_log(
            phone=clean_user_phone,
            actor_role="elder",
            action="LOGIN_SUCCESS",
            details=f"Senior {patient.name} logged in."
        )

        return {
            "status": "success",
            "role": "elder",
            "phone": clean_user_phone,
            "patient": patient,
            "message": f"Welcome, {patient.name}! Your personalized health companion is ready."
        }
    else:
        # Caregiver / Family mode
        target_patient_phone = "".join(c for c in (req.patient_phone or "") if c.isdigit())
        if not target_patient_phone:
            target_patient_phone = "9849012345"
        
        patient = db.get_or_create_patient(target_patient_phone, name="Senior Parent", role="patient")
        
        # Add caregiver if not already present
        existing_cg = next((c for c in patient.caregivers if c.phone == clean_user_phone), None)
        if not existing_cg:
            from app.models import Caregiver
            new_cg = Caregiver(
                id=f"cg_{clean_user_phone}",
                name=req.name or "Family Caregiver",
                relationship="Caregiver",
                phone=clean_user_phone,
                email=f"caregiver_{clean_user_phone}@example.com",
                role=req.role
            )
            patient.caregivers.append(new_cg)

        db.add_activity_log(
            phone=target_patient_phone,
            actor_role=req.role,
            action="CAREGIVER_CONNECTED",
            details=f"{req.name or 'Caregiver'} ({clean_user_phone}) linked to {patient.name}."
        )

        return {
            "status": "success",
            "role": req.role,
            "caregiver_phone": clean_user_phone,
            "caregiver_name": req.name or "Family Caregiver",
            "linked_patient_phone": target_patient_phone,
            "patient": patient,
            "message": f"Connected to patient {patient.name} ({target_patient_phone})."
        }

@router.post("/verify-passcode", response_model=PasscodeResponse)
def verify_passcode(req: VerifyPasscodeRequest):
    """
    Constant-time PBKDF2 passcode verification with 5-attempt rate-limiting lockout.
    Zero insecure backdoors (0000 removed).
    """
    clean_phone = "".join(c for c in (req.phone or "9849012345") if c.isdigit())
    
    # Check lockout
    is_locked, rem = security_service.is_locked_out(clean_phone)
    if is_locked:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Security lockout active. Try again in {rem} seconds."
        )

    patient = db.get_patient(clean_phone)
    
    # Secure verification
    is_valid = security_service.verify_passcode(req.passcode, patient.passcode)
    
    if is_valid:
        security_service.reset_failed_attempts(clean_phone)
        db.add_activity_log(clean_phone, "caretaker", "AUTH_PASSCODE_SUCCESS", "Passcode verified successfully.")
        return PasscodeResponse(authenticated=True, role="caregiver", patient=patient)
    else:
        fails = security_service.record_failed_attempt(clean_phone)
        remaining_attempts = max(0, security_service.MAX_ATTEMPTS - fails)
        db.add_activity_log(clean_phone, "system", "AUTH_PASSCODE_FAILED", f"Invalid passcode attempt. Remaining: {remaining_attempts}")
        
        if fails >= security_service.MAX_ATTEMPTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed attempts. Security lockout triggered for 15 minutes."
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid family passcode. {remaining_attempts} attempts remaining before lockout."
        )
