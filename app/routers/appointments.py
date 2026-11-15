import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel
from app.database import db
from app.models import Appointment
from app.services.email_service import email_engine

router = APIRouter(prefix="/api/appointments", tags=["Doctor Appointments"])

class CreateAppointmentRequest(BaseModel):
    doctor_name: str
    specialty: str
    hospital: str
    phone: Optional[str] = ""
    date: str  # "YYYY-MM-DD"
    time: str  # "HH:MM"
    notes: Optional[str] = ""
    patient_phone: Optional[str] = None

@router.get("", response_model=List[Appointment])
def list_appointments(phone: Optional[str] = Query(None)):
    return db.get_appointments(phone)

@router.post("", response_model=Appointment)
def create_appointment(req: CreateAppointmentRequest):
    appt_id = f"appt_{uuid.uuid4().hex[:8]}"
    appt = Appointment(
        id=appt_id,
        doctor_name=req.doctor_name,
        specialty=req.specialty,
        hospital=req.hospital,
        phone=req.phone or "",
        date=req.date,
        time=req.time,
        notes=req.notes or "",
        status="scheduled"
    )
    result = db.add_appointment(appt, phone=req.patient_phone)
    
    # Proactively send appointment confirmation email to caregivers
    pat = db.get_patient(req.patient_phone)
    subj = f"📅 Doctor Appointment Scheduled: {pat.name} with {req.doctor_name}"
    body = f"""
    <h3>Doctor Consultation Scheduled</h3>
    <p><strong>Patient:</strong> {pat.name}</p>
    <p><strong>Doctor:</strong> {req.doctor_name} ({req.specialty})</p>
    <p><strong>Hospital / Clinic:</strong> {req.hospital}</p>
    <p><strong>Date & Time:</strong> {req.date} at {req.time}</p>
    <p><strong>Notes:</strong> {req.notes or 'None'}</p>
    """
    for cg in pat.caregivers:
        if cg.email:
            email_engine.send_email(cg.email, subj, body, "appointment_new", f"appt_new_{appt_id}")

    return result

@router.delete("/{appt_id}")
def cancel_appointment(appt_id: str, phone: Optional[str] = Query(None)):
    success = db.delete_appointment(appt_id, phone)
    if not success:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"status": "success", "message": f"Appointment {appt_id} cancelled."}

@router.get("/{appt_id}/ics")
def download_ics_calendar(appt_id: str, phone: Optional[str] = Query(None)):
    """Generates standard RFC-5545 iCalendar (.ics) file for 1-click import into Google / Apple Calendar."""
    appts = db.get_appointments(phone)
    appt = next((a for a in appts if a.id == appt_id), None)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    clean_date = appt.date.replace("-", "")
    clean_time = appt.time.replace(":", "") + "00"
    dtstart = f"{clean_date}T{clean_time}"

    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//VayoCare//Elder Medical Appointments//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:{appt.id}@vayocare.health
DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{dtstart}
SUMMARY:Dr. {appt.doctor_name} ({appt.specialty}) - Medical Consultation
DESCRIPTION:Consultation at {appt.hospital}. Notes: {appt.notes}
LOCATION:{appt.hospital}
STATUS:CONFIRMED
BEGIN:VALARM
TRIGGER:-PT2H
ACTION:DISPLAY
DESCRIPTION:Reminder: Doctor appointment in 2 hours
END:VALARM
END:VEVENT
END:VCALENDAR
""".replace("\n", "\r\n")

    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename=appointment_{appt_id}.ics"}
    )
