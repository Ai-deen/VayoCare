from app.services.audit_service import audit_service

def test_audit_detects_missing_ecosprin():
    prescription = "Rx: Tab Telmikem 40 1-0-0, Tab Glycomet 500 1-0-1, Tab Ecosprin 75 0-1-0. Review in 30 days."
    chemist_strips = "Chemist Bill: Telmikem 40 (10 tabs), Glycomet 500 (10 tabs)."

    res = audit_service.audit_prescription_and_strips(prescription, chemist_strips)
    
    assert len(res.discrepancies) > 0
    missing = [d for d in res.discrepancies if d.issue_type == "missing_medicine"]
    assert any("Ecosprin" in m.medicine_name for m in missing)
    assert res.confidence_score >= 0.90

def test_audit_refill_runway():
    prescription = "Rx: Tab Telmikem 40, Tab Shelcal 500"
    chemist_strips = "Chemist: Telmikem 40, Shelcal 500"

    res = audit_service.audit_prescription_and_strips(prescription, chemist_strips)
    assert len(res.refill_runway) > 0
    # Urgent items (<= 3 days remaining) should appear first
    assert res.refill_runway[0].days_left <= res.refill_runway[-1].days_left
