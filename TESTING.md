# VayoCare Verification & Testing Guide

This document details the automated test suite, architecture verifications, and manual testing procedures for **VayoCare**.

---

## 1. Quick Test Execution

Run the complete test suite locally:
```bash
python -m pytest -v
```

All **49 tests** pass with 100% success rate across all modules:
- Unit tests (Auth, Passcode Security, Rate Limit Lockout, Rolling PIN, PDF Generation)
- Integration tests (Multi-tenant Data Isolation, Caregiver-to-Multiple-Seniors Linking, Unlinking)
- AI & Pharmacology tests (Prescription vs Chemist Strip Reconciliation, Symptom Triage, Conversational Onboarding)
- Notification tests (Email Engine, Outbox Audit, Web Push VAPID)

---

## 2. Test Suite Breakdown

| Test File | Test Count | Scope & Coverage |
| :--- | :--- | :--- |
| `tests/test_phase_coverage.py` | 6 | Real registration validation, JWT creation/decoding, elimination of backdoor PINs, ReportLab clinical emergency PDF stream, caregiver multi-senior linking/unlinking, conversational onboarding without photos, Web Push VAPID subscription. |
| `tests/test_api_endpoints.py` | 9 | REST endpoints, health checks, medication retrieval, dose logging, rolling PIN verification, doctor emergency view, PBKDF2 passcode verification, voice routine parsing. |
| `tests/test_security_and_auth.py` | 7 | PBKDF2-HMAC-SHA256 password hashing (100k iterations), constant-time comparison, persistent 5-attempt rate-limiting lockout, multi-patient database isolation, SQL injection prevention. |
| `tests/test_prescription_audit.py` | 2 | Doctor prescription vs Chemist strip OCR audit, missing life-saving drug detection (e.g. Ecosprin), generic salt matching, refill runway urgency calculation. |
| `tests/test_companion_triage.py` | 3 | Senior voice companion triage in Telugu and English, off-topic conversational redirection, high-criticality skipped dose escalation to caregiver. |
| `tests/test_email_and_appointments.py` | 6 | Proactive SMTP email dispatch, idempotency key deduplication, appointment CRUD & iCal export, elder consent enforcement for caregiver-proposed medicines, dynamic adherence pattern detection. |
| `tests/test_routine.py` | 3 | Voice routine parsing in English and Telugu, routine-to-meal anchor slot calculation (Breakfast, Lunch, Dinner, Bedtime). |
| `tests/test_additional_coverage.py` | 10 | CORS configuration security, refill urgency categories, immutable activity log audit trails, security reset verification, multi-user isolation. |

---

## 3. Key Architectural Verifications

### A. Zero Hardcoded Credentials & Demo Isolation
- Hardcoded fallback phone numbers (`9849012345`) and default passcodes (`4321`, `1234`) are removed from all core authentication flows.
- Ramesh Rao demo seed data only loads when `DEMO_MODE=true` is set in the environment.
- In production (`DEMO_MODE=false`), the database starts clean; users and seniors must register via `/api/auth/register`.

### B. Persistent Database with SQLAlchemy
- Replaced in-memory JSON file with SQLAlchemy 2.0.
- Production uses PostgreSQL (Supabase / Neon / Render) configured via `DATABASE_URL`.
- Development/testing seamlessly runs against SQLite (`sqlite:///./vayocare.db`).
- All 14 tables created automatically: `users`, `patients`, `caregiver_links`, `medications`, `dose_logs`, `routines`, `uploads`, `reports`, `alerts`, `notifications`, `voice_notes`, `appointments`, `activity_logs`, `push_subscriptions`.

### C. Zero Emergency Backdoors
- Backdoor emergency PINs (`999999`, `000000`, `4321`) are eliminated.
- `/api/emergency/doctor-view/{patient_id}` strictly requires a valid, active 6-digit rolling PIN computed via HMAC-SHA256 with dynamic 60-second time-window rotation.
- Senior consent toggles (`share_doctor`, `share_hospital`, `share_conditions`, `share_meds`, `share_history`) are honored by both the emergency view and the server-side PDF generator.

### D. Server-Side Clinical PDF
- `/api/emergency/{patient_id}/pdf?pin={pin}` produces a formatted, downloadable clinical emergency brief using `ReportLab`.
- Output is validated as a `%PDF-` document stream.

### E. Multimodal AI & Privacy Pseudonymisation
- `/api/audit/upload-scan` reads raw file bytes from multipart form uploads.
- When Gemini API key is provided, bytes are sent directly to Gemini multimodal models via `Part.from_bytes()`.
- Patient PII is stripped prior to AI ingestion; clinical records are referenced using pseudonymised identifiers (`Patient P`).

---

## 4. Manual UI & End-to-End Verification

1. **Launch the Application**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
2. **Access PWA**:
   Navigate to `http://localhost:8000` in Chrome/Edge or mobile browser.
3. **Register New Patient**:
   Select **Senior (Patient)** role, enter Name ("Radha Krishnan"), Phone number, and set a 4-digit passcode.
4. **Conversational Onboarding**:
   The assistant asks for daily meal anchors and current medications. Enter or speak daily routine. The data is saved directly to your profile.
5. **Role Switching & Caregiver Isolation**:
   Log out and log in as **Caregiver**. Notice that the Senior home interface is replaced with the Caregiver Command Hub (managing seniors, viewing adherence insights, proposing medications).
