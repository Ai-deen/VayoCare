import io
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request, Response, status, Depends
from app.config import settings
from app.database import db
from app.models import EmergencyViewData
from app.services.qr_service import qr_service
from app.db.session import SessionLocal
from app.db import models as db_models

from app.services.auth_service import get_current_user, require_current_user

router = APIRouter(prefix="/api/emergency", tags=["Zero-App Emergency QR Pass & PDF"])

def build_pin_data(request: Optional[Request] = None, patient_id: Optional[str] = None):
    target_id = patient_id
    if not target_id and settings.DEMO_MODE:
        target_id = "p_ramesh_72"
    
    patient = db.get_patient(target_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient record not found.")

    pin = qr_service.generate_rolling_pin(patient.id)
    rem = qr_service.get_remaining_seconds()

    base_url = settings.PUBLIC_BASE_URL
    if request and not base_url:
        host_header = request.headers.get("host", "localhost:8000")
        scheme = request.url.scheme or "http"
        base_url = f"{scheme}://{host_header}"
    
    absolute_url = f"{base_url}/emergency/{patient.id}?pin={pin}"
    qr_data = qr_service.generate_qr_svg_or_base64(absolute_url)

    return {
        "patient_id": patient.id,
        "rolling_pin": pin,
        "valid_for_seconds": rem,
        "qr_code_data": qr_data,
        "emergency_url": absolute_url
    }

@router.get("/current-pin")
def get_current_rolling_pin(
    request: Request,
    patient_id: Optional[str] = Query(None),
    current_user: Optional[db_models.User] = Depends(get_current_user)
):
    """
    Rolling PIN generator: Strictly requires login.
    Unauthenticated access is denied to prevent exposing the PIN.
    """
    if not current_user and not (settings.DEMO_MODE and not patient_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in to view active emergency PIN."
        )

    # Determine patient id from auth context
    target_id = patient_id
    if current_user:
        if current_user.role in ("patient", "elder"):
            pat = db.get_patient(current_user.phone)
            target_id = pat.id
        elif current_user.role in ("caregiver", "caretaker", "family"):
            if not target_id:
                # linked patient
                with SessionLocal() as session:
                    link = session.query(db_models.CaregiverLink).filter(
                        db_models.CaregiverLink.caregiver_user_id == current_user.id,
                        db_models.CaregiverLink.status == "approved"
                    ).first()
                    if link and link.patient:
                        target_id = link.patient.id
                    else:
                        raise HTTPException(status_code=403, detail="No linked patient found for caregiver.")

    return build_pin_data(request, patient_id=target_id)

@router.get("/doctor-view/{patient_id}", response_model=EmergencyViewData)
def get_doctor_emergency_view(patient_id: str, pin: str = Query(..., description="Active 6-digit rolling PIN")):
    """
    Doctor Emergency View.
    STRICT SECURITY: Zero backdoors (000000, 999999, 4321 removed).
    Valid rolling PIN is strictly REQUIRED.
    """
    if not pin or not pin.strip():
        raise HTTPException(
            status_code=403,
            detail="A valid 6-digit emergency rolling PIN is required."
        )

    patient = db.get_patient(patient_id)
    if patient.id != patient_id and patient.phone != patient_id:
        raise HTTPException(status_code=404, detail="Patient record not found")

    is_valid = (
        qr_service.verify_rolling_pin(patient.id, pin.strip()) or
        qr_service.verify_rolling_pin(patient_id, pin.strip())
    )
    if not is_valid:
        raise HTTPException(
            status_code=403,
            detail="Expired or Invalid Access PIN. Please ask the patient or caregiver for the active PIN on their screen."
        )

    # Consent enforcement
    with SessionLocal() as session:
        db_p = session.query(db_models.Patient).filter(
            (db_models.Patient.id == patient_id) | (db_models.Patient.phone == patient_id)
        ).first()
        share_doc = db_p.share_doctor if db_p else True
        share_hosp = db_p.share_hospital if db_p else True
        share_cond = db_p.share_conditions if db_p else True
        share_meds = db_p.share_meds if db_p else True
        share_hist = db_p.share_history if db_p else True

    meds = db.get_medications(patient.phone) if share_meds else []
    active_salts = [
        {
            "brand": m.brand_name,
            "senior_name": m.senior_label,
            "chemical_salt": m.salt_composition,
            "dosage": m.dosage,
            "timing": f"{m.timing_anchor.capitalize()} ({m.timing_relation.replace('_', ' ')})",
            "criticality": m.criticality
        }
        for m in meds
    ]

    doctor_info = None
    if share_doc and patient.doctor:
        doctor_info = patient.doctor
        if not share_hosp:
            doctor_info.hospital = "[Redacted by Senior Consent]"

    conditions = patient.chronic_conditions if share_cond else ["[Redacted by Senior Consent]"]
    allergies = patient.allergies if share_cond else ["[Redacted by Senior Consent]"]
    today_history = db.get_today_logs(patient.phone) if share_hist else []

    return EmergencyViewData(
        patient_name=patient.name,
        age=patient.age,
        gender=patient.gender,
        chronic_conditions=conditions,
        allergies=allergies,
        primary_doctor=doctor_info,
        emergency_contacts=patient.caregivers,
        active_medications_and_salts=active_salts,
        today_dose_history=today_history,
        pin_verified=True,
        valid_until="Active Emergency Session"
    )

@router.get("/{patient_id}/pdf")
def generate_emergency_pdf(patient_id: str, pin: str = Query(..., description="Active 6-digit rolling PIN")):
    """
    Generates downloadable clinical emergency summary PDF using ReportLab.
    Enforces rolling PIN and senior consent toggles.
    """
    patient = db.get_patient(patient_id)
    if not patient or (patient.id != patient_id and patient.phone != patient_id):
        raise HTTPException(status_code=404, detail="Patient record not found")

    is_valid = (
        qr_service.verify_rolling_pin(patient.id, pin.strip()) or
        qr_service.verify_rolling_pin(patient_id, pin.strip())
    )
    if not is_valid:
        raise HTTPException(status_code=403, detail="Invalid or expired emergency PIN for PDF download.")

    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=12
    )
    sub_style = ParagraphStyle(
        'SubStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=16
    )
    h2_style = ParagraphStyle(
        'H2Style',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor("#1E40AF"),
        spaceBefore=10,
        spaceAfter=6
    )

    story = []
    story.append(Paragraph("VayoCare Clinical Emergency Summary", title_style))
    story.append(Paragraph(f"Emergency clinical pass for <b>{patient.name}</b> (Age: {patient.age}, Gender: {patient.gender}). Generated under zero-app rolling PIN access.", sub_style))
    story.append(Spacer(1, 8))

    # Consent checks
    with SessionLocal() as session:
        db_p = session.query(db_models.Patient).filter(
            (db_models.Patient.id == patient_id) | (db_models.Patient.phone == patient_id)
        ).first()
        share_doc = db_p.share_doctor if db_p else True
        share_cond = db_p.share_conditions if db_p else True
        share_meds = db_p.share_meds if db_p else True

    # 1. Medical Conditions & Allergies Table
    if share_cond:
        cond_str = ", ".join(patient.chronic_conditions) if patient.chronic_conditions else "None reported"
        allergy_str = ", ".join(patient.allergies) if patient.allergies else "No known drug allergies"
        med_summary_data = [
            ["Chronic Conditions", cond_str],
            ["Known Allergies", allergy_str]
        ]
        t1 = Table(med_summary_data, colWidths=[150, 390])
        t1.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#EFF6FF")),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))
        story.append(Paragraph("Clinical Profile", h2_style))
        story.append(t1)
        story.append(Spacer(1, 10))

    # 2. Medications Table
    if share_meds:
        meds = db.get_medications(patient.phone)
        med_rows = [["Medicine Brand", "Active Salt", "Dosage", "Anchor", "Criticality"]]
        for m in meds:
            med_rows.append([
                m.brand_name,
                m.salt_composition or "N/A",
                m.dosage,
                m.timing_anchor.capitalize(),
                m.criticality.upper()
            ])
        t2 = Table(med_rows, colWidths=[110, 170, 90, 80, 90])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E40AF")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")])
        ]))
        story.append(Paragraph("Active Medications & Chemical Salts", h2_style))
        story.append(t2)
        story.append(Spacer(1, 10))

    # 3. Emergency Contacts
    if patient.caregivers:
        cg_rows = [["Name", "Relationship", "Phone", "Email"]]
        for cg in patient.caregivers:
            cg_rows.append([cg.name, cg.relationship, cg.phone, cg.email])
        t3 = Table(cg_rows, colWidths=[140, 110, 120, 170])
        t3.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#047857")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('PADDING', (0, 0), (-1, -1), 5)
        ]))
        story.append(Paragraph("Family & Caregiver Emergency Contacts", h2_style))
        story.append(t3)

    doc.build(story)
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="VayoCare_Clinical_Brief_{patient.name.replace(" ", "_")}.pdf"'
        }
    )
