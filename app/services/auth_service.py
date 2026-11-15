from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from fastapi import Depends, HTTPException, Security, status
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
    Extracts authenticated User from Bearer token if present.
    Returns None if token is missing or invalid (allows non-breaking optional auth for public endpoints).
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
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token."
        )
    return current_user

def verify_caregiver_access(caregiver_user: db_models.User, patient_id: str, db: Session) -> bool:
    """Verifies that the caregiver has an approved link to the patient."""
    link = db.query(db_models.CaregiverLink).filter(
        db_models.CaregiverLink.caregiver_user_id == caregiver_user.id,
        db_models.CaregiverLink.patient_id == patient_id,
        db_models.CaregiverLink.status == "approved"
    ).first()
    return link is not None
