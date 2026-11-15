# 🔒 VayoCare Security & Privacy Architecture

VayoCare is designed from the ground up to protect vulnerable elderly patients and their families with defense-in-depth security.

---

## 1. Authentication & Credential Storage
- **Passcode Hashing:** All passcodes are hashed using industry-standard **PBKDF2-HMAC-SHA256** with 100,000 iterations and cryptographically secure random 16-byte salts (`app/services/security_service.py`).
- **No Plaintext Passcodes:** Passcodes are never stored or logged in plain text.
- **Zero Backdoors:** No bypass codes or hardcoded magic pins (e.g. `0000`) exist in production authentication.

## 2. Brute-Force Protection & Rate Limiting
- **5-Attempt Lockout:** Accounts are automatically locked out for **15 minutes (900 seconds)** upon 5 consecutive failed authentication attempts.
- **Constant-Time Verification:** Passcode comparisons use `hmac.compare_digest` to prevent timing-attack side-channel leaks.

## 3. Granular Role-Based Access Control (RBAC) & Elder Consent
- **Three Distinct Roles:**
  - `elder` (Patient): Has full consent control, routine management, dose logging, and approval rights.
  - `caretaker`: Can view adherence, schedule doctor appointments, propose medications, and run prescription audits.
  - `family`: Read-only adherence overview and speed dial access.
- **Elder Consent & Control:** Any medication proposed by a caretaker remains in `pending_approval` status until the senior explicitly approves it on their device.

## 4. Input Sanitization & Anti-Injection
- Phone numbers and identifiers are strictly normalized and sanitized against SQL/NoSQL injection vectors (`app/database.py`).
- Pydantic v2 runtime type validation guarantees strict schema adherence across all inbound REST payloads.

## 5. Proactive Email Engine & Idempotency Safeguards
- Proactive dose and appointment reminders use unique **Idempotency Keys** (`app/services/email_service.py`) to guarantee that no duplicate email is ever sent.
- Comprehensive outbound audit logs record every communication dispatched.

## 6. Zero-App Emergency QR Pass Privacy
- Paramedics and ER doctors access only essential active chemical salts, today's dose log, and emergency speed dials without app installation.
- Personal chats, private habits, and non-clinical transcripts are strictly excluded from emergency brief payloads.

## 7. Reporting Security Vulnerabilities
If you discover a security vulnerability, please report it privately to `security@vayocare.health`.
