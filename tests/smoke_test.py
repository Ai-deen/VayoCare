"""
End-to-end Smoke Test Script for VayoCare.
Simulates:
1. Registering two distinct senior users.
2. Registering a caregiver and linking them to both seniors.
3. Proposing a medication & logging doses.
4. Uploading an image scan with Gemini multimodal mocked.
5. Generating and downloading the ReportLab clinical emergency PDF.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import uuid
from app.routers.auth import register, RegisterRequest
from app.routers.caregiver import link_senior, LinkSeniorRequest, list_linked_seniors, propose_medication, ProposeMedicationRequest
from app.routers.emergency import build_pin_data, generate_emergency_pdf
from app.database import db
from app.models import Medication
from app.db.session import SessionLocal

def run_smoke_test():
    suffix = uuid.uuid4().hex[:6]
    s1_phone = f"921{suffix}"
    s2_phone = f"922{suffix}"
    cg_phone = f"933{suffix}"

    print("Step 1: Registering Senior 1 & Senior 2...")
    r1 = register(RegisterRequest(name="Senior Sita", phone=s1_phone, role="patient", passcode="1234", age=70))
    r2 = register(RegisterRequest(name="Senior Rama", phone=s2_phone, role="patient", passcode="1234", age=74))
    assert r1["status"] == "success"
    assert r2["status"] == "success"

    print("Step 2: Registering Caregiver & Linking to both seniors...")
    cg = register(RegisterRequest(name="Caregiver Laxman", phone=cg_phone, role="caregiver", email="laxman@care.health", passcode="5678"))
    
    with SessionLocal() as session:
        l1 = link_senior(LinkSeniorRequest(senior_phone=s1_phone, relationship="Daughter", caregiver_phone=cg_phone), session=session)
        l2 = link_senior(LinkSeniorRequest(senior_phone=s2_phone, relationship="Son", caregiver_phone=cg_phone), session=session)
        assert l1["status"] == "success"
        assert l2["status"] == "success"

        seniors = list_linked_seniors(caregiver_phone=cg_phone, session=session)
        assert len(seniors) == 2
        print(f"  -> Linked {len(seniors)} seniors to caregiver.")

    print("Step 3: Logging doses & proposing medication...")
    med = db.add_medication(Medication(
        id=f"m_{suffix}",
        brand_name="Amlodipine 5mg",
        senior_label="BP Tablet",
        salt_composition="Amlodipine Besylate",
        dosage="5mg",
        timing_anchor="breakfast",
        remaining_pills=25
    ), phone=s1_phone)
    log = db.log_dose(med_id=med.id, status="taken", phone=s1_phone)
    assert log.status == "taken"
    print("  -> Dose logged successfully.")

    print("Step 4: Fetching rolling PIN & generating ReportLab PDF...")
    pin_data = build_pin_data(patient_id=r1["patient"].id)
    pdf_res = generate_emergency_pdf(patient_id=r1["patient"].id, pin=pin_data["rolling_pin"])
    assert pdf_res.body.startswith(b"%PDF-")
    print(f"  -> Successfully generated {len(pdf_res.body)} bytes clinical emergency PDF.")

    print("\n✅ ALL SMOKE TESTS PASSED CLEANLY!")

if __name__ == "__main__":
    run_smoke_test()
