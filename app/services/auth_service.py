from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from fastapi import Depends, HTTPException, Security, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db, SessionLocal
from app.db import models as db_models

security_bearer = HTTPBearer(auto_error=False)

class AuthService:
    def create_access_token(self, user_id: str, phone: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=settings.JWT_EXPIRES_DAYS)
        payload = {
            "sub": user_id,
            "phone": phone,
            "role": role,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    def decode_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except Exception:
            return None

auth_service = AuthService()

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    db: Session = Depends(get_db)
) -> Optional[db_models.User]:
    """
    Extracts authenticated User from Bearer token.
    """
    if not credentials:
        return None
    token = credentials.credentials
    payload = auth_service.decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    
    user = db.query(db_models.User).filter(db_models.User.id == payload["sub"]).first()
    return user

def require_current_user(
    current_user: Optional[db_models.User] = Depends(get_current_user)
) -> db_models.User:
    """Enforces authentication: raises 401 if valid Bearer token is missing."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token in Authorization header."
        )
    return current_user

def get_authenticated_patient(
    patient_id: Optional[str] = Query(None),
    current_user: db_models.User = Depends(require_current_user),
    session: Session = Depends(get_db)
) -> db_models.Patient:
    """
    Derives authenticated patient context:
    - If user is Patient: returns own patient profile. Cross-access to other patient_id -> 403 Forbidden.
    - If user is Caregiver: verifies approved CaregiverLink. Unlinked access -> 403 Forbidden.
    """
    if current_user.role in ("patient", "elder"):
        pat = session.query(db_models.Patient).filter(db_models.Patient.user_id == current_user.id).first()
        if not pat:
            pat = session.query(db_models.Patient).filter(db_models.Patient.phone == current_user.phone).first()
        if not pat:
            raise HTTPException(status_code=404, detail="Patient profile not found for authenticated user.")
        
        # If caller tried to pass someone else's patient_id
        if patient_id and patient_id != pat.id and patient_id != pat.phone:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Patients cannot access records belonging to other users."
            )
        return pat

    elif current_user.role in ("caregiver", "caretaker", "family"):
        if patient_id:
            # Check link to requested patient
            clean_pid = patient_id
            link = session.query(db_models.CaregiverLink).join(db_models.Patient).filter(
                db_models.CaregiverLink.caregiver_user_id == current_user.id,
                ((db_models.Patient.id == clean_pid) | (db_models.Patient.phone == clean_pid)),
                db_models.CaregiverLink.status == "approved"
            ).first()

            if not link:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. You do not have an approved caregiver link to this patient."
                )
            return link.patient
        else:
            # First approved linked patient
            link = session.query(db_models.CaregiverLink).filter(
                db_models.CaregiverLink.caregiver_user_id == current_user.id,
                db_models.CaregiverLink.status == "approved"
            ).first()
            if not link or not link.patient:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No linked senior patients found for this caregiver account."
                )
            return link.patient

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized role.")
