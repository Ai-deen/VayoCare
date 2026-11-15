# 🧓 ArogyaMitra (ఆరోగ్య మిత్ర)
### Smart Elderly Care & Routine-Anchored Medication Management Companion

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![PWA Ready](https://img.shields.io/badge/PWA-Installable-5A0FC8?logo=pwa&logoColor=white)](https://web.dev/progressive-web-apps/)
[![Google Cloud Run](https://img.shields.io/badge/Google%20Cloud-Run-4285F4?logo=google-cloud&logoColor=white)](https://cloud.google.com/run)
[![Tests Passing](https://img.shields.io/badge/Tests-20%2F20%20Passing-brightgreen?logo=pytest)](./tests)

---

## 📌 Problem Statement Alignment (PromptWars x Catalyst)

Traditional reminder apps fail Indian seniors because:
1. **Seniors don't live by rigid clock alarms** — their lives revolve around natural daily routines (*Tiffin / Breakfast, Afternoon Lunch, Night Dinner*).
2. **Language & Interaction Barriers** — rigid English forms and alarms cause anxiety or confusion; seniors code-switch between Telugu, Hindi, and English (*"మీరు tiffin తిన్నారా? Tablet వేసుకున్నారా?"*).
3. **Conversational Straying & Privacy** — seniors frequently ramble when asked a question, while personal chatter should remain private and clinical symptoms should be immediately triaged.
4. **Prescription vs Chemist Discrepancies** — medicines bought from local pharmacies often have mismatched salts, missing strips, or run out unnoticed.
5. **ER & Clinic Blind Spots** — doctors and paramedics during an emergency cannot install an app just to see a patient's active medication salts.

**ArogyaMitra** solves all of this with an accessible, mobile-first Progressive Web App (PWA) powered by Python (FastAPI) and Google Gemini AI.

---

## 🌟 The 3 Winning Unique Selling Propositions (USPs)

### 🎙️ USP 1: Multilingual "Routine-Anchored" Voice Companion
- **Routine Triggers**: Seniors speak their daily routine once (*"I wake up at 8, eat tiffin around 9"*). Medication reminders anchor around meals rather than rigid alarms.
- **Native Code-Switched Voice Check-In**: Greets warmly in Telugu, Hindi, or English, showing large high-contrast tablet cards and pill colors.
- **Smart Off-Topic Redirect & Clinical Severity Triage**:
  - If the senior chats about shopping or friends (*"బయటకు వెళ్లి బట్టలు కొన్నాను..."*), the AI gently acknowledges it, filters out personal talk, and steers them back to their medication.
  - Triage Engine differentiates **High Criticality** medications (Blood Pressure, Diabetes, Heart meds like *Telmikem 40, Glycomet 500, Ecosprin 75*) from **Low Criticality** supplements (*Shelcal 500, Neurobion*). Skipped vital medications immediately alert family caregivers via email and SMS.

### 🔍 USP 2: "Prescription-vs-Strip" Dual Smart Audit & Refill Runway
- **Dual Photo Scan**: Caregivers snap a photo of the doctor's prescription and photos of the chemist medicine strips bought.
- **AI Chemical Salt Cross-Reconciliation**: Gemini cross-references active salts, dosages, and quantities to immediately detect missing items (e.g. missing blood thinners) or generic salt discrepancies.
- **Visual Refill Runway**: Calculates remaining supply days and displays an urgent 1-click refill card with pack photos to show directly at the pharmacy.

### 🚨 USP 3: App-Independent "ER & Doctor" QR Pass (With Rolling PIN)
- **Zero-App Emergency View**: Scanning the senior's QR code opens a mobile browser emergency brief on any smartphone — **no app download required**.
- **Rolling 6-Digit PIN**: Dynamic TOTP-style passcode rolling every 60 seconds gives seniors privacy control.
- **Clinical Doctor Brief**:
  1. Active Medications & Chemical Salt Compositions (prevents lethal adverse drug interactions).
  2. Today's Dose Log (prevents accidental double-dosing).
  3. 1-Tap Emergency Family & Doctor Speed Dials.
  4. 1-Tap Downloadable/Printable Clinical Health Brief.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Mobile-First Phone PWA                      │
│   • Web Speech Recognition (Telugu / Hindi / English)       │
│   • Native Web Audio Text-to-Speech (TTS)                   │
│   • Offline-First Service Worker + manifest.json            │
│   • Accessible UI (High contrast, 48px+ touch targets)      │
└──────────────────────────────▲──────────────────────────────┘
                               │ JSON REST API
┌──────────────────────────────▼──────────────────────────────┐
│                    Python FastAPI Backend                   │
│   ├── /api/auth       -> Passcode-Protected Family Access   │
│   ├── /api/routine    -> Voice Daily Routine Parsing        │
│   ├── /api/companion  -> Off-Topic Redirect & Triage        │
│   ├── /api/medications-> Adherence & Dose Logging           │
│   ├── /api/audit      -> Dual Scan Salt Reconciliation      │
│   ├── /api/emergency  -> Rolling PIN & Zero-App View        │
│   └── /api/alerts     -> Proactive Caretaker Escalations    │
├─────────────────────────────────────────────────────────────┤
│ Google Gemini 2.5 Flash │ In-Memory / SQLite │ Dockerized   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 6-Slide Pitch Framework (From Hackathon Guidelines)

1. **Slide 1 - Problem**: 75% of Indian elderly miss doses due to rigid alarm times, language friction, and prescription-vs-chemist mismatches.
2. **Slide 2 - Evidence**: 1 out of 3 hospital readmissions for chronic seniors stem from preventable medication non-adherence and drug clashing.
3. **Slide 3 - Cost of Problem**: ₹1,20,000+ per emergency hospitalization for avoidable cardiac/diabetic crises.
4. **Slide 4 - Solution**: ArogyaMitra — the multilingual, routine-anchored PWA companion that bridges seniors, caregivers, and doctors.
5. **Slide 5 - Before vs After**:
   - *Before*: Rigid alarms ignored, 13 hours to discover a missed BP pill, zero drug visibility during emergencies.
   - *After*: Routine-anchored voice check-in, real-time caregiver alerts in <3 minutes, zero-app rolling PIN emergency pass.
6. **Slide 6 - The 3 USPs**:
   - Routine-Anchored Voice Companion (Telugu/Hindi/English)
   - Dual-Scan Salt Reconciliation & Refill Runway
   - Zero-App Doctor QR Pass with Rolling PIN.

---

## 🚀 Quickstart Guide (Local Development)

### 1. Prerequisites
- Python 3.11+
- Git

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/your-username/arogyamitra.git
cd arogyamitra

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the PWA Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open `http://localhost:8000` on your mobile phone or browser.

---

## 🧪 Automated Testing (100% Pass)

Run the full automated test suite:
```bash
pytest -v
```
All 20 test suites pass across:
- Voice routine natural language parsing
- Multilingual voice check-in and off-topic redirect
- Criticality-based clinical severity triage
- Prescription-vs-strip AI discrepancy auditing
- Dynamic rolling PIN generation and verification
- End-to-end API endpoints and passcode security

---

## ☁️ Google Cloud Run Deployment

To deploy on Google Cloud Run:
```bash
# Build & Deploy directly to Cloud Run
gcloud run deploy arogyamitra \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
```

---

## 🔒 Security & Privacy Practices
- **Numeric Passcode Access**: Shared family/caregiver access protected by 4-digit PIN.
- **Granular Consent Rolling PIN**: Doctors only receive access to active salts through a 60-second rolling TOTP code.
- **Privacy Guardrail**: Senior's personal conversations (family news, shopping) are discarded from clinical logging.

---

## 👥 Hackathon Team & Acknowledgements
Built for **PromptWars x Catalyst** by Google for Developers & MnM.
