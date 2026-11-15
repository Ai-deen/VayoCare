import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Boolean, Float, DateTime, Text, JSON, ForeignKey
)
from sqlalchemy.orm import relationship
from app.db.session import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    phone = Column(String(32), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    email = Column(String(128), nullable=True)
    role = Column(String(32), default="patient")  # "patient", "caregiver", "doctor", "admin"
    hashed_passcode = Column(String(256), nullable=False)
    failed_attempts = Column(Integer, default=0)
    lockout_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    patient_profile = relationship("Patient", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    push_subscriptions = relationship("PushSubscription", back_populates="user", cascade="all, delete-orphan")

class Patient(Base):
    __tablename__ = "patients"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(128), nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String(32), nullable=True)
    phone = Column(String(32), unique=True, index=True, nullable=False)
    emergency_contact = Column(String(32), nullable=True)
    language_preference = Column(String(16), default="en")
    chronic_conditions = Column(JSON, default=list)  # list of strings
    allergies = Column(JSON, default=list)  # list of strings
    
    # Doctor info
    doctor_name = Column(String(128), default="Dr. Primary Care")
    doctor_specialty = Column(String(128), default="General Physician")
    doctor_hospital = Column(String(128), default="Local Clinic")
    doctor_phone = Column(String(32), default="")

    # Consent toggles for emergency / doctor view
    share_doctor = Column(Boolean, default=True)
    share_hospital = Column(Boolean, default=True)
    share_conditions = Column(Boolean, default=True)
    share_meds = Column(Boolean, default=True)
    share_history = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="patient_profile")
    routine = relationship("Routine", back_populates="patient", uselist=False, cascade="all, delete-orphan")
    medications = relationship("Medication", back_populates="patient", cascade="all, delete-orphan")
    dose_logs = relationship("DoseLog", back_populates="patient", cascade="all, delete-orphan")
    caregiver_links = relationship("CaregiverLink", back_populates="patient", cascade="all, delete-orphan")
    voice_notes = relationship("VoiceNote", back_populates="patient", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="patient", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="patient", cascade="all, delete-orphan")
    uploads = relationship("Upload", back_populates="patient", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="patient", cascade="all, delete-orphan")

class CaregiverLink(Base):
    __tablename__ = "caregiver_links"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    caregiver_user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(String(64), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type = Column("relationship", String(64), default="Caregiver")
    status = Column(String(32), default="approved")  # "pending", "approved", "rejected"
    can_manage_meds = Column(Boolean, default=True)
    notify_missed_dose = Column(Boolean, default=True)
    notify_low_stock = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="caregiver_links")
    caregiver_user = relationship("User")

class Routine(Base):
    __tablename__ = "routines"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    patient_id = Column(String(64), ForeignKey("patients.id", ondelete="CASCADE"), unique=True, nullable=False)
    wake_up = Column(String(16), default="07:30")
    breakfast = Column(String(16), default="09:00")
    lunch = Column(String(16), default="13:30")
    dinner = Column(String(16), default="20:30")
    bedtime = Column(String(16), default="22:00")
    notes = Column(Text, default="Configured routine")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = relationship("Patient", back_populates="routine")

class Medication(Base):
    __tablename__ = "medications"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    patient_id = Column(String(64), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    brand_name = Column(String(128), nullable=False)
    senior_label = Column(String(128), nullable=False)
    senior_label_te = Column(String(128), nullable=True)
    senior_label_hi = Column(String(128), nullable=True)
    salt_composition = Column(String(256), nullable=True)
    dosage = Column(String(64), default="1 tablet")
    timing_anchor = Column(String(32), default="breakfast")  # breakfast, lunch, dinner, bedtime
    timing_relation = Column(String(32), default="after_food")  # before_food, after_food, with_food
    criticality = Column(String(16), default="high")  # high, low
    remaining_pills = Column(Integer, default=10)
    daily_doses = Column(Integer, default=1)
    pill_color = Column(String(32), default="#3B82F6")
    purpose = Column(String(128), default="General health")
    approval_status = Column(String(32), default="approved")  # approved, pending_approval, rejected
    added_by = Column(String(32), default="elder")  # elder, caretaker, doctor
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="medications")

class DoseLog(Base):
    __tablename__ = "dose_logs"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    patient_id = Column(String(64), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    medication_id = Column(String(64), nullable=False, index=True)
    medication_name = Column(String(128), nullable=False)
    senior_label = Column(String(128), nullable=False)
    timing_anchor = Column(String(32), default="breakfast")
    status = Column(String(32), default="pending")  # taken, skipped, pending
    logged_at = Column(DateTime, nullable=True)
    feedback_notes = Column(Text, default="")
    triage_action = Column(String(64), default="none")
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="dose_logs")

class Upload(Base):
    __tablename__ = "uploads"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    patient_id = Column(String(64), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    uploader_id = Column(String(64), nullable=True)
    file_name = Column(String(256), nullable=False)
    file_url = Column(String(512), nullable=False)
    file_size = Column(Integer, default=0)
    mime_type = Column(String(64), default="application/octet-stream")
    file_category = Column(String(64), default="prescription")  # prescription, strip, test_report
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="uploads")

class Report(Base):
    __tablename__ = "reports"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    patient_id = Column(String(64), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    report_type = Column(String(64), default="clinical_summary")  # clinical_summary, audit_report, refill_card
    summary_data = Column(JSON, default=dict)
    file_url = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="reports")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    patient_id = Column(String(64), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    severity = Column(String(32), default="info")  # info, warning, critical
    title = Column(String(256), nullable=False)
    message = Column(Text, nullable=False)
    recipient_email = Column(String(128), default="")
    status = Column(String(32), default="sent")  # pending, sent, delivered, failed
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="alerts")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(64), default="reminder")  # reminder, alert, approval_request, system
    is_read = Column(Boolean, default=False)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")

class VoiceNote(Base):
    __tablename__ = "voice_notes"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    patient_id = Column(String(64), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    caregiver_id = Column(String(64), nullable=True)
    caregiver_name = Column(String(128), default="Caregiver")
    message_text = Column(Text, nullable=False)
    assigned_anchor = Column(String(32), default="breakfast")
    audio_url = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="voice_notes")

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    patient_id = Column(String(64), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_name = Column(String(128), nullable=False)
    specialty = Column(String(128), default="General Physician")
    hospital = Column(String(128), default="Local Clinic")
    phone = Column(String(32), default="")
    date = Column(String(32), nullable=False)  # YYYY-MM-DD
    time = Column(String(16), nullable=False)  # HH:MM
    notes = Column(Text, default="")
    status = Column(String(32), default="scheduled")  # scheduled, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="appointments")

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    patient_id = Column(String(64), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_role = Column(String(32), default="elder")  # elder, caretaker, doctor, system
    action = Column(String(64), nullable=False)
    details = Column(Text, default="")
    timestamp = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="activity_logs")

class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    endpoint = Column(Text, nullable=False)
    p256dh = Column(Text, nullable=False)
    auth = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="push_subscriptions")
