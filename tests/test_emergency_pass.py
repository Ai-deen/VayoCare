from app.services.qr_service import qr_service

def test_generate_and_verify_rolling_pin():
    patient_id = "p_ramesh_72"
    pin = qr_service.generate_rolling_pin(patient_id)
    assert len(pin) == 6
    assert pin.isdigit()
    assert qr_service.verify_rolling_pin(patient_id, pin) is True

def test_invalid_pin_rejected():
    patient_id = "p_ramesh_72"
    assert qr_service.verify_rolling_pin(patient_id, "999998") is False

def test_qr_generation():
    url = "/emergency/p_ramesh_72?pin=123456"
    qr_data = qr_service.generate_qr_svg_or_base64(url)
    assert qr_data.startswith("data:image/png;base64,") or qr_data.startswith("http")
