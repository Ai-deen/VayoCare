from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel
from app.models import PrescriptionAuditResponse
from app.services.audit_service import audit_service

router = APIRouter(prefix="/api/audit", tags=["Prescription vs Chemist Strip Audit"])

class AuditTextRequest(BaseModel):
    prescription_text: str
    strip_text: str

@router.post("/reconcile", response_model=PrescriptionAuditResponse)
def reconcile_prescription(req: AuditTextRequest):
    return audit_service.audit_prescription_and_strips(
        req.prescription_text,
        req.strip_text
    )

@router.post("/upload-scan", response_model=PrescriptionAuditResponse)
async def upload_dual_scans(
    prescription_file: Optional[UploadFile] = File(None),
    strip_file: Optional[UploadFile] = File(None),
    prescription_notes: Optional[str] = Form(""),
    strip_notes: Optional[str] = Form("")
):
    """
    Simulates / processes photo upload of doctor prescription & chemist strip.
    """
    rx_text = prescription_notes or "Rx: Tab Telmikem 40 1-0-0 (BP), Tab Glycomet 500 1-0-1 (Diabetes), Tab Ecosprin 75 0-1-0 (Cardio). Next review 30 days."
    st_text = strip_notes or "Chemist Receipt & Strips: Telmikem 40 (10 tabs), Glycomet 500 (10 tabs). (Note: Ecosprin 75 not in stock/not purchased)."
    
    return audit_service.audit_prescription_and_strips(rx_text, st_text)
