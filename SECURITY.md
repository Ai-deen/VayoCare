# 🔒 VayoCare Security & Privacy Architecture

VayoCare is designed from the ground up to protect elderly patients and their families with defense-in-depth security, strict privacy boundaries, and medical data governance.

---

## 1. Authentication & Credential Storage
- **Passcode Hashing:** All passcodes are hashed using industry-standard **PBKDF2-HMAC-SHA256** with 100,000 iterations and cryptographically secure random 16-byte salts (`app/services/security_service.py`).
- **No Plaintext Passcodes:** Passcodes are never stored or logged in plain text.
- **JWT Session Tokens:** Authenticated endpoints verify signed JWT bearer tokens (`app/services/auth_service.py`) with configurable expiry.
- **Zero Backdoors:** Emergency backdoor PINs (`999999`, `000000`, `4321`) are eliminated from the codebase.

## 2. Brute-Force Protection & Database-Persisted Lockout
- **5-Attempt Lockout:** Accounts are automatically locked out for **15 minutes (900 seconds)** upon 5 consecutive failed authentication attempts.
- **Persistent Lockout:** Lockouts are persisted directly in the `users` table (`failed_attempts`, `lockout_until`) so brute-force tracking survives application restarts and scale-outs.
- **Constant-Time Verification:** Passcode comparisons use `hmac.compare_digest` to prevent timing-attack side-channel leaks.

## 3. Granular Role-Based Access Control (RBAC) & Elder Consent
- **Distinct Roles:**
  - `patient` / `elder`: Has full consent control, routine management, dose logging, and medication approval rights.
  - `caregiver`: Can view adherence, schedule doctor appointments, propose medications, and run prescription audits only for verified linked seniors.
  - `unlinked`: Rejects access to unlinked patient profiles with `403 Forbidden`.
- **Elder Consent & Control:** Any medication proposed by a caretaker remains in `pending_approval` status until the senior explicitly approves it on their device.
- **Senior Consent Toggles:** Seniors can independently toggle clinical data visibility (`share_doctor`, `share_hospital`, `share_conditions`, `share_meds`, `share_history`) for emergency and PDF views.

## 4. Input Sanitization & Anti-Injection
- Phone numbers and identifiers are strictly normalized and sanitized against SQL injection vectors via SQLAlchemy 2.0 parameterized queries.
- Pydantic v2 runtime type validation guarantees strict schema adherence across all inbound REST payloads.

## 5. Proactive Email Engine & Idempotency Safeguards
- Proactive dose and appointment reminders use unique **Idempotency Keys** (`app/services/email_service.py`) to guarantee that no duplicate email is ever sent.
- Comprehensive outbound audit logs record every communication dispatched.

## 6. Zero-App Emergency QR Pass & Server-Side PDF
- Paramedics and ER doctors access only essential active chemical salts, today's dose log, and emergency speed dials without app installation.
- Strictly requires a valid, active 6-digit rolling PIN computed via HMAC-SHA256 with 60-second time-window rotation.
- Secure ReportLab clinical PDF generation honors all active senior consent toggles.

## 7. AI Privacy & Pseudonymisation
- Patient PII (name, phone number, address) is stripped prior to sending prescription images to Google Gemini multimodal models.
- Clinical records are referenced using pseudonymised identifiers (`Patient P`).

## 8. Reporting Security Vulnerabilities
If you discover a security vulnerability, please report it privately to `security@vayocare.health`.
