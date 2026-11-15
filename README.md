# 🧓 VayoCare (వయోకేర్)
### Smart Elderly Care & Routine-Anchored Medication Management Companion

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![PWA Ready](https://img.shields.io/badge/PWA-Installable-5A0FC8?logo=pwa&logoColor=white)](https://web.dev/progressive-web-apps/)
[![Google Gemini AI](https://img.shields.io/badge/Gemini-3.5_Flash-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)
[![Tests Passing](https://img.shields.io/badge/Tests-20%2F20%20Passing-brightgreen?logo=pytest)](./tests)

---

## 📌 Problem Statement (PromptWars x Catalyst)

Traditional reminder apps fail Indian seniors because:
1. **Seniors don't follow rigid clock alarms** — their lives revolve around daily routines (*Tiffin / Breakfast, Afternoon Lunch, Night Dinner*).
2. **Language & Interaction Barriers** — English-only forms cause anxiety; seniors code-switch between Telugu, Hindi, and English (*"మీరు tiffin తిన్నారా? Tablet వేసుకున్నారా?"*).
3. **Conversational Straying & Privacy** — seniors ramble when asked a question; personal chatter should remain private, clinical symptoms should be triaged immediately.
4. **Prescription vs Chemist Discrepancies** — medicines from local pharmacies often have mismatched salts, missing strips, or run out unnoticed.
5. **ER & Clinic Blind Spots** — doctors during an emergency cannot install an app just to see a patient's active medication salts.

**VayoCare** solves this with an accessible, mobile-first PWA powered by Python (FastAPI) and Google Gemini AI.

---

## 🌟 3 Unique Selling Propositions (USPs)

### 🎙️ USP 1: Multilingual Routine-Anchored Voice Companion
- **Routine Triggers**: Seniors speak their daily routine once. Medication reminders anchor around meals, not rigid alarms.
- **Native Code-Switched Voice Check-In**: Greets in Telugu, Hindi, or English with large high-contrast tablet cards and pill colors.
- **Senior-Friendly Labels**: "BP మాత్ర" (BP Tablet), not "Telmisartan 40mg" — zero jargon.
- **Smart Off-Topic Redirect & Clinical Triage**:
  - Gently acknowledges off-topic talk (shopping, friends), filters it out, steers back to medication.
  - Triage Engine differentiates **High Criticality** meds (BP, Diabetes, Heart) from **Low Criticality** supplements (Calcium, Vitamins). Skipped vital meds immediately alert family caregivers.

### 🔍 USP 2: Prescription-vs-Strip Dual AI Audit & Refill Runway
- **Dual Photo Scan**: Snap doctor's prescription + chemist medicine strips.
- **AI Salt Cross-Reconciliation**: Gemini compares active salts, dosages, quantities — flags missing items (e.g., missing blood thinners).
- **Visual Refill Runway**: Shows remaining supply days with urgency color-coding.

### 🚨 USP 3: Zero-App Emergency QR Pass (Rolling PIN)
- **Zero-App Emergency View**: Scanning the QR opens a browser-based medical brief on any smartphone — **no app download needed**.
- **Rolling 6-Digit PIN**: TOTP-style code rolling every 60 seconds for privacy.
- **Doctor Brief**: Active meds with chemical salts, today's dose log, emergency contacts.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Mobile-First PWA (Phone)                   │
│   • Web Speech Recognition (Telugu / Hindi / English)       │
│   • Text-to-Speech (TTS) native audio                      │
│   • Offline-First Service Worker + manifest.json            │
│   • Senior-accessible UI (high contrast, 48px+ targets)    │
└──────────────────────────────▲──────────────────────────────┘
                               │ JSON REST API
┌──────────────────────────────▼──────────────────────────────┐
│                    Python FastAPI Backend                   │
│   ├── /api/auth       → Phone login & passcode access      │
│   ├── /api/routine    → Voice daily routine parsing         │
│   ├── /api/companion  → AI chat, off-topic redirect, triage│
│   ├── /api/medications→ Adherence tracking & dose logging   │
│   ├── /api/audit      → Prescription vs strip reconciliation│
│   ├── /api/emergency  → Rolling PIN & zero-app doctor view  │
│   └── /api/alerts     → Caretaker email/SMS escalations     │
├─────────────────────────────────────────────────────────────┤
│  Google Gemini 3.5 Flash │ In-Memory DB │ Docker / CloudRun │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quickstart

### Prerequisites
- Python 3.11+

### Install & Run
```bash
git clone https://github.com/Ai-deen/vayocare.git
cd vayocare
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open `http://localhost:8000` on your phone or browser.

---

## 🧪 Test Suite (20/20 Passing)

```bash
pytest -v
```

Covers:
- Voice routine parsing (English/Telugu)
- Multilingual companion chat & off-topic redirect
- Clinical severity triage escalation
- Prescription-vs-strip AI audit
- Rolling PIN generation & verification
- All API endpoints & passcode security

---

## ☁️ Deployment (Google Cloud Run)

```bash
gcloud run deploy vayocare \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars GEMINI_API_KEY="YOUR_KEY"
```

---

## 🔒 Security & Privacy
- **Phone-based auth** with numeric passcode
- **Rolling PIN** (60s TOTP) for emergency QR access
- **Privacy guardrail**: Personal conversations filtered from clinical logs

---

## 📊 Pitch Framework (6 Slides)
1. **Problem**: 75% of Indian elderly miss doses due to rigid alarms & language barriers
2. **Evidence**: 1/3 hospital readmissions from preventable medication non-adherence
3. **Cost**: ₹1,20,000+ per avoidable emergency hospitalization
4. **Solution**: VayoCare — routine-anchored, multilingual PWA companion
5. **Before → After**: Rigid alarms ignored → meal-anchored voice check-in; 13hr discovery gap → real-time alerts
6. **3 USPs**: Voice Companion + Dual Audit + Zero-App QR Pass

---

## 👥 Team
Built for **PromptWars x Catalyst** by Google for Developers & MnM.
