from app.services.triage_service import triage_service
from app.database import db

def test_companion_dose_marked_taken_telugu():
    patient = db.get_patient()
    res = triage_service.process_companion_input(
        patient=patient,
        user_speech="హా టిఫిన్ అయిపోయింది, టాబ్లెట్ వేసుకున్నాను",
        language="te",
        anchor="breakfast"
    )
    assert res.action_taken == "dose_marked_taken"
    assert "చాలా మంచిది" in res.reply_text

def test_companion_offtopic_redirect_shopping():
    patient = db.get_patient()
    # Elderly wanders off-topic about buying clothes and friends
    res = triage_service.process_companion_input(
        patient=patient,
        user_speech="నేను ఈరోజు బయటకు వెళ్లి బట్టలు కొన్నాను, నా స్నేహితుడు కలిశాడు",
        language="te",
        anchor="breakfast"
    )
    assert res.redirected_offtopic is True
    assert "tablet" in res.reply_text.lower() or "వేసుకున్నారా" in res.reply_text

def test_companion_critical_skipped_escalation():
    patient = db.get_patient()
    # Missed high criticality BP dose
    res = triage_service.process_companion_input(
        patient=patient,
        user_speech="లేదు నాకు తినాలని లేదు, మందులు వేసుకోలేదు",
        language="te",
        anchor="breakfast"
    )
    assert res.action_taken == "caregiver_alerted"
    assert res.criticality == "high"
    # Ensure an alert was added in database
    latest_alert = db.get_alerts()[0]
    assert latest_alert.severity == "critical"
