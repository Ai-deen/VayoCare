import uuid
import pytest
from fastapi import HTTPException
from app.db.session import SessionLocal
from app.db import models as db_models
from app.routers.auth import register, RegisterRequest
from app.routers.emergency import get_current_rolling_pin
from app.routers.audit import get_uploaded_file
from app.services.auth_service import auth_service, require_current_user, get_authenticated_patient

def test_unauthenticated_current_pin_rejected_when_not_demo(monkeypatch):
    """Verifies that anonymous users cannot fetch rolling PINs."""
    from app.config import settings
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    
    with pytest.raises(HTTPException) as exc:
        get_current_rolling_pin(request=None, patient_id="p_other_user", current_user=None)
    assert exc.value.status_code == 401

def test_cross_patient_authorization_isolation():
    """Verifies that Patient A cannot access Patient B's records."""
    phone_a = f"910{uuid.uuid4().int % 10000000:07d}"
    phone_b = f"910{uuid.uuid4().int % 10000000:07d}"

    # Register Patient A
    res_a = register(RegisterRequest(
        name="Patient Alpha",
        phone=phone_a,
        role="patient",
        passcode="1122"
    ))
    user_a_id = res_a["user"]["id"]
    pat_a_id = res_a["patient"].id

    # Register Patient B
    res_b = register(RegisterRequest(
        name="Patient Beta",
        phone=phone_b,
        role="patient",
        passcode="3344"
    ))
    user_b_id = res_b["user"]["id"]
    pat_b_id = res_b["patient"].id

    with SessionLocal() as session:
        user_a = session.query(db_models.User).filter(db_models.User.id == user_a_id).first()
        
        # User A accessing their own patient context succeeds
        pat = get_authenticated_patient(patient_id=pat_a_id, current_user=user_a, session=session)
        assert pat.id == pat_a_id

        # User A trying to access User B's patient_id raises 403 Forbidden!
        with pytest.raises(HTTPException) as exc:
            get_authenticated_patient(patient_id=pat_b_id, current_user=user_a, session=session)
        assert exc.value.status_code == 403

def test_unlinked_caregiver_rejected_with_403():
    """Verifies that an unlinked Caregiver cannot access an unlinked Senior."""
    cg_phone = f"989{uuid.uuid4().int % 10000000:07d}"
    senior_phone = f"977{uuid.uuid4().int % 10000000:07d}"

    # Register Caregiver
    cg_res = register(RegisterRequest(
        name="Unlinked Carer",
        phone=cg_phone,
        role="caregiver",
        passcode="9900",
        email="unlinked@family.health"
    ))
    cg_user_id = cg_res["user"]["id"]

    # Register Senior
    sen_res = register(RegisterRequest(
        name="Independent Senior",
        phone=senior_phone,
        role="patient",
        passcode="5566"
    ))
    senior_pat_id = sen_res["patient"].id

    with SessionLocal() as session:
        cg_user = session.query(db_models.User).filter(db_models.User.id == cg_user_id).first()
        
        # Caregiver trying to access unlinked senior raises 403 Forbidden!
        with pytest.raises(HTTPException) as exc:
            get_authenticated_patient(patient_id=senior_pat_id, current_user=cg_user, session=session)
        assert exc.value.status_code == 403

def test_private_uploaded_file_authorization():
    """Verifies that uploaded prescription files reject unauthorized users."""
    user_phone = f"944{uuid.uuid4().int % 10000000:07d}"
    other_phone = f"955{uuid.uuid4().int % 10000000:07d}"

    reg_owner = register(RegisterRequest(name="File Owner", phone=user_phone, role="patient", passcode="1234"))
    reg_other = register(RegisterRequest(name="Other User", phone=other_phone, role="patient", passcode="1234"))

    owner_id = reg_owner["user"]["id"]
    other_id = reg_other["user"]["id"]

    with SessionLocal() as session:
        owner_user = session.query(db_models.User).filter(db_models.User.id == owner_id).first()
        other_user = session.query(db_models.User).filter(db_models.User.id == other_id).first()

        # Create dummy upload record belonging to owner
        up = db_models.Upload(
            id=f"up_{uuid.uuid4().hex}",
            patient_id=reg_owner["patient"].id,
            file_name="rx_secret.jpg",
            file_url="/api/audit/file/rx_secret.jpg",
            mime_type="image/jpeg"
        )
        session.add(up)
        session.commit()

        # Other user trying to access owner's upload raises 403 Forbidden!
        with pytest.raises(HTTPException) as exc:
            get_uploaded_file("rx_secret.jpg", current_user=other_user, session=session)
        assert exc.value.status_code == 403
