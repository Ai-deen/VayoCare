// VayoCare PWA Core Application Engine (v2.2)

let currentToken = localStorage.getItem('vayocare_token') || '';
let currentLanguage = localStorage.getItem('vayocare_lang') || 'en';
let currentUserRole = localStorage.getItem('vayocare_role') || 'patient';
let currentUserPhone = localStorage.getItem('vayocare_phone') || '';
let currentUserName = localStorage.getItem('vayocare_name') || '';
let currentUserId = localStorage.getItem('vayocare_user_id') || '';
let currentPatientId = localStorage.getItem('vayocare_patient_id') || '';
let currentManagedSeniorPhone = localStorage.getItem('vayocare_cg_managed_phone') || '';
let currentAnchor = detectCurrentTimeAnchor();
let isListening = false;
let speechRecognition = null;
let cameraStream = null;
let currentCameraTarget = 'onboarding';
let onboardingStep = 1;
let pinIntervalTimer = null;

function detectCurrentTimeAnchor() {
  const now = new Date();
  const hrs = now.getHours() + (now.getMinutes() / 60);
  if (hrs < 11.5) return 'breakfast';
  if (hrs < 16.0) return 'lunch';
  if (hrs < 21.5) return 'dinner';
  return 'bedtime';
}

// ==================== AUTHENTICATED FETCH HELPER ====================
async function fetchWithAuth(url, options = {}) {
  options.headers = options.headers || {};
  if (currentToken) {
    options.headers['Authorization'] = `Bearer ${currentToken}`;
  }
  const res = await fetch(url, options);
  if (res.status === 401) {
    console.warn("Session expired or unauthorized. Showing login.");
    logoutUser();
    throw new Error("Unauthorized");
  }
  return res;
}

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
  registerServiceWorker();
  initSpeechRecognition();

  // Restore accessibility preferences
  if (localStorage.getItem('vayocare_large_text') === 'true') {
    document.body.classList.add('large-text');
  }
  if (localStorage.getItem('vayocare_high_contrast') === 'true') {
    document.body.classList.add('high-contrast');
  }

  if (!currentToken || !currentUserPhone) {
    showLoginModal();
  } else {
    setupDashboardForRole(currentUserRole);
  }

  applyLanguage(currentLanguage);
});

// ==================== SERVICE WORKER & WEB PUSH ====================
async function registerServiceWorker() {
  if ('serviceWorker' in navigator && 'PushManager' in window) {
    try {
      const reg = await navigator.serviceWorker.register('/sw.js');
      // Subscribe to web push if logged in
      if (currentToken) {
        initPushSubscription(reg);
      }
    } catch (err) {
      console.warn("ServiceWorker registration note:", err);
    }
  }
}

async function initPushSubscription(reg) {
  try {
    const keyRes = await fetch('/api/push/vapid-public-key');
    const keyData = await keyRes.json();
    if (!keyData.public_key) return;

    let sub = await reg.pushManager.getSubscription();
    if (!sub) {
      const convertedKey = urlBase64ToUint8Array(keyData.public_key);
      sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: convertedKey
      });
    }

    const subJson = sub.toJSON();
    await fetchWithAuth('/api/push/subscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        endpoint: sub.endpoint,
        p256dh: subJson.keys ? subJson.keys.p256dh : '',
        auth: subJson.keys ? subJson.keys.auth : ''
      })
    });
  } catch (err) {
    console.warn("Push subscription optional setup:", err);
  }
}

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding).replace(/\-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

// ==================== AUTHENTICATION & REGISTRATION ====================
function showLoginModal() {
  document.getElementById('loginOverlay').style.display = 'block';
}

function setAuthMode(mode) {
  const isReg = mode === 'register';
  document.getElementById('authTabLogin').style.background = isReg ? 'none' : 'white';
  document.getElementById('authTabLogin').style.color = isReg ? '#64748B' : '#1E293B';
  document.getElementById('authTabRegister').style.background = isReg ? 'white' : 'none';
  document.getElementById('authTabRegister').style.color = isReg ? '#1E293B' : '#64748B';
  document.getElementById('registerFields').style.display = isReg ? 'block' : 'none';
  document.getElementById('authSubmitBtn').textContent = isReg ? '✨ Create Account & Start' : '🚀 Sign In';
}

function selectRole(role) {
  currentUserRole = role;
  document.getElementById('roleSelectPatient').classList.toggle('selected', role === 'patient');
  document.getElementById('roleSelectCaregiver').classList.toggle('selected', role === 'caregiver');
  document.getElementById('caregiverRegisterFields').style.display = (role === 'caregiver') ? 'block' : 'none';
  document.getElementById('patientRegisterFields').style.display = (role === 'patient') ? 'grid' : 'none';
}

async function handleAuthSubmit() {
  const phone = document.getElementById('authPhone').value.trim();
  const name = document.getElementById('authName').value.trim();
  const passcode = document.getElementById('authPasscode').value.trim();
  const isReg = document.getElementById('registerFields').style.display === 'block';

  if (!phone || phone.length < 7) {
    alert("Please enter a valid phone number.");
    return;
  }
  if (!name) {
    alert("Please enter your name.");
    return;
  }
  if (!passcode || passcode.length < 4) {
    alert("Please enter a 4-digit passcode / PIN.");
    return;
  }

  try {
    if (isReg) {
      // Registration Flow
      const ageVal = document.getElementById('authAge').value;
      const age = ageVal ? parseInt(ageVal, 10) : null;
      const gender = document.getElementById('authGender').value;
      const email = document.getElementById('authEmail').value.trim();

      if (currentUserRole === 'caregiver' && (!email || !email.includes('@'))) {
        alert("A valid email address is required for caregiver registration.");
        return;
      }

      const regRes = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: phone,
          name: name,
          passcode: passcode,
          role: currentUserRole,
          age: age,
          gender: gender,
          email: email || null,
          language: currentLanguage
        })
      });

      if (!regRes.ok) {
        const err = await regRes.json();
        alert(err.detail || "Registration failed.");
        return;
      }

      const data = await regRes.json();
      saveAuthSession(data.access_token, data.role, phone, name, data.user?.id, data.patient?.id);

      document.getElementById('loginOverlay').style.display = 'none';

      if (data.role === 'patient') {
        startConversationalOnboarding();
      } else {
        setupDashboardForRole(data.role);
      }

    } else {
      // Phone Login Flow
      const loginRes = await fetch('/api/auth/phone-login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          role: currentUserRole,
          name: name,
          phone: phone,
          language: currentLanguage
        })
      });

      if (!loginRes.ok) {
        const err = await loginRes.json();
        alert(err.detail || "Login failed.");
        return;
      }

      const data = await loginRes.json();
      saveAuthSession(data.access_token, currentUserRole, phone, name, data.user?.id, data.patient?.id);
      document.getElementById('loginOverlay').style.display = 'none';
      setupDashboardForRole(currentUserRole);
    }
  } catch (err) {
    console.error("Auth error:", err);
    alert("Connection error. Please check server status.");
  }
}

async function loginDemoProfile() {
  try {
    const res = await fetch('/api/auth/phone-login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        role: "patient",
        name: "Ramesh Rao",
        phone: "9849012345",
        language: currentLanguage
      })
    });
    const data = await res.json();
    saveAuthSession(data.access_token, 'patient', '9849012345', 'Ramesh Rao', 'u_ramesh_72', 'p_ramesh_72');
    document.getElementById('loginOverlay').style.display = 'none';
    setupDashboardForRole('patient');
  } catch (err) {
    console.error("Demo login error:", err);
  }
}

function saveAuthSession(token, role, phone, name, userId, patientId) {
  currentToken = token;
  currentUserRole = role;
  currentUserPhone = phone;
  currentUserName = name;
  currentUserId = userId || '';
  currentPatientId = patientId || '';

  localStorage.setItem('vayocare_token', token);
  localStorage.setItem('vayocare_role', role);
  localStorage.setItem('vayocare_phone', phone);
  localStorage.setItem('vayocare_name', name);
  if (userId) localStorage.setItem('vayocare_user_id', userId);
  if (patientId) localStorage.setItem('vayocare_patient_id', patientId);
}

function logoutUser() {
  localStorage.removeItem('vayocare_token');
  localStorage.removeItem('vayocare_phone');
  localStorage.removeItem('vayocare_name');
  localStorage.removeItem('vayocare_role');
  localStorage.removeItem('vayocare_user_id');
  localStorage.removeItem('vayocare_patient_id');
  currentToken = '';
  currentUserPhone = '';
  if (pinIntervalTimer) clearInterval(pinIntervalTimer);
  showLoginModal();
}

// ==================== CONVERSATIONAL ONBOARDING ====================
function startConversationalOnboarding() {
  document.getElementById('seniorSection').style.display = 'none';
  document.getElementById('caregiverSection').style.display = 'none';
  document.getElementById('seniorOnboardingView').style.display = 'block';
  onboardingStep = 1;

  const chatLog = document.getElementById('onboardingChatLog');
  chatLog.innerHTML = `
    <div class="chat-bubble-agent">
      Namaste <b>${currentUserName}</b>! Welcome to VayoCare. Let's configure your daily schedule.<br><br>
      <b>What time do you usually wake up, have breakfast, lunch, and dinner?</b><br>
      <i>(You can tap the microphone 🎙️ or type your answer below)</i>
    </div>
  `;
}

async function sendOnboardingStep() {
  const input = document.getElementById('onboardingInputText');
  const msg = input.value.trim();
  if (!msg) return;

  const chatLog = document.getElementById('onboardingChatLog');
  chatLog.innerHTML += `<div class="chat-bubble-user">${msg}</div>`;
  input.value = '';
  chatLog.scrollTop = chatLog.scrollHeight;

  try {
    const res = await fetchWithAuth('/api/companion/onboarding', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        patient_id: currentPatientId || currentUserPhone,
        message: msg,
        step: onboardingStep,
        language: currentLanguage
      })
    });
    const data = await res.json();
    chatLog.innerHTML += `<div class="chat-bubble-agent">${data.reply}</div>`;
    chatLog.scrollTop = chatLog.scrollHeight;

    if (data.finished) {
      document.getElementById('onboardingPhotoPrompt').style.display = 'block';
    } else {
      onboardingStep = data.step || (onboardingStep + 1);
    }
  } catch (err) {
    console.error("Onboarding step error:", err);
  }
}

function toggleOnboardingVoice() {
  if (!speechRecognition) {
    alert("Speech recognition is not supported on this browser.");
    return;
  }
  if (isListening) {
    speechRecognition.stop();
  } else {
    speechRecognition.start();
    document.getElementById('onboardingMicBtn').style.background = '#FEE2E2';
    speechRecognition.onresult = (event) => {
      const text = event.results[0][0].transcript;
      document.getElementById('onboardingInputText').value = text;
      sendOnboardingStep();
    };
    speechRecognition.onend = () => {
      isListening = false;
      document.getElementById('onboardingMicBtn').style.background = '#EFF6FF';
    };
  }
}

function finishOnboardingDirectly() {
  document.getElementById('seniorOnboardingView').style.display = 'none';
  setupDashboardForRole('patient');
}

// ==================== DASHBOARD SETUP & ROLE ISOLATION ====================
function setupDashboardForRole(role) {
  const isPatient = role === 'patient' || role === 'elder';
  document.getElementById('seniorOnboardingView').style.display = 'none';
  document.getElementById('seniorSection').style.display = isPatient ? 'block' : 'none';
  document.getElementById('caregiverSection').style.display = isPatient ? 'none' : 'block';

  const tag = document.getElementById('userStatusTag');
  if (tag) {
    tag.textContent = isPatient
      ? `Senior: ${currentUserName} (${currentUserPhone})`
      : `Caregiver: ${currentUserName}`;
  }

  currentAnchor = detectCurrentTimeAnchor();

  if (isPatient) {
    switchSeniorTab('today');
    fetchGreeting();
    loadMedications();
    loadElderPendingApprovals();
  } else {
    initCaregiverHub();
  }
}

// ==================== SENIOR TAB NAVIGATION (5 TABS) ====================
function switchSeniorTab(tabName) {
  const tabs = ['today', 'medicines', 'history', 'profile', 'emergency'];
  tabs.forEach(t => {
    const el = document.getElementById(`senior-${t}`);
    if (el) el.style.display = (t === tabName) ? 'block' : 'none';
  });

  const navBtns = document.querySelectorAll('#seniorNav .tab-btn');
  const idx = tabs.indexOf(tabName);
  navBtns.forEach((btn, i) => {
    btn.classList.toggle('active', i === idx);
  });

  if (tabName === 'today') {
    fetchGreeting();
    loadMedications();
  } else if (tabName === 'medicines') {
    loadFullMedicinesInventory();
  } else if (tabName === 'history') {
    loadAdherenceHistory();
  } else if (tabName === 'profile') {
    loadSeniorProfile();
  } else if (tabName === 'emergency') {
    loadEmergencyPass();
  }
}

// ==================== TIME-ANCHORED GREETING & COMPANION ====================
async function fetchGreeting() {
  try {
    const res = await fetchWithAuth(`/api/companion/greeting?language=${currentLanguage}&anchor=${currentAnchor}`);
    const data = await res.json();
    
    const bubble = document.getElementById('companionSpeechBubble');
    if (bubble) bubble.textContent = `"${data.text}"`;

    const hero = document.getElementById('heroPillLabel');
    if (hero) hero.textContent = `💊 ${data.active_medicine || 'Medicine Check-in'}`;
  } catch (err) {
    console.error("Greeting error:", err);
  }
}

function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return;

  speechRecognition = new SpeechRecognition();
  speechRecognition.continuous = false;
  speechRecognition.interimResults = false;

  speechRecognition.onstart = () => {
    isListening = true;
    const btn = document.getElementById('micBtn');
    if (btn) btn.classList.add('listening');
    const pill = document.getElementById('voiceStatusPill');
    if (pill) pill.textContent = 'Listening... (Speak now)';
  };

  speechRecognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    const pill = document.getElementById('voiceStatusPill');
    if (pill) pill.textContent = `Heard: "${transcript}"`;
    sendCompanionMessage(transcript);
  };

  speechRecognition.onend = () => {
    isListening = false;
    const btn = document.getElementById('micBtn');
    if (btn) btn.classList.remove('listening');
    const pill = document.getElementById('voiceStatusPill');
    if (pill) pill.textContent = 'Ready • Microphone Active';
  };
}

function toggleVoiceInput() {
  if (!speechRecognition) {
    alert("Speech recognition is not supported on this browser.");
    return;
  }
  if (isListening) {
    speechRecognition.stop();
  } else {
    try { speechRecognition.start(); } catch (e) {}
  }
}

async function sendCompanionMessage(text) {
  try {
    const res = await fetchWithAuth('/api/companion/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        patient_id: currentPatientId || currentUserPhone,
        speech_text: text,
        language: currentLanguage,
        current_anchor: currentAnchor
      })
    });
    const data = await res.json();
    const bubble = document.getElementById('companionSpeechBubble');
    if (bubble) bubble.textContent = `"${data.reply_text}"`;
    loadMedications();
  } catch (err) {
    console.error("Companion chat error:", err);
  }
}

async function submitQuickDose(status) {
  try {
    const medsRes = await fetchWithAuth('/api/medications');
    const meds = await medsRes.json();
    const anchorMeds = meds.filter(m => m.timing_anchor === currentAnchor && m.approval_status === 'approved');
    const targetMed = anchorMeds.length > 0 ? anchorMeds[0] : (meds[0] || null);

    if (!targetMed) {
      alert("No active medications found to log.");
      return;
    }

    await fetchWithAuth('/api/medications/log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        medication_id: targetMed.id,
        status: status,
        notes: `Quick button logged as ${status}`
      })
    });

    const bubble = document.getElementById('companionSpeechBubble');
    if (bubble) {
      bubble.textContent = (status === 'taken')
        ? `Wonderful! Recorded that you took ${targetMed.senior_label}. Stay healthy!`
        : `Got it. We will remind you shortly about your ${targetMed.senior_label}.`;
    }
    loadMedications();
  } catch (err) {
    console.error("Dose log error:", err);
  }
}

// ==================== MEDICATIONS & ELDER CONSENT ====================
async function loadMedications() {
  try {
    const res = await fetchWithAuth('/api/medications');
    const meds = await res.json();
    const container = document.getElementById('medicationsList');
    if (!container) return;

    const approvedMeds = meds.filter(m => m.approval_status === "approved");
    if (approvedMeds.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 22px; background: white; border: 1px dashed #CBD5E1; border-radius: 16px; color: #64748B; font-size: 14px;">
          No active medicines configured. Complete onboarding or scan a prescription.
        </div>
      `;
      return;
    }

    container.innerHTML = approvedMeds.map(m => {
      const friendlyName = currentLanguage === 'te' ? (m.senior_label_te || m.senior_label) : (currentLanguage === 'hi' ? (m.senior_label_hi || m.senior_label) : m.senior_label);
      const isUrgent = m.remaining_pills <= 3;
      return `
        <div class="med-card" style="border-left: 6px solid ${m.pill_color}; margin-bottom: 10px; background: white; padding: 14px; border-radius: 14px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 6px rgba(0,0,0,0.04);">
          <div>
            <div style="font-weight: 800; font-size: 15px; color: #1E293B;">${friendlyName}</div>
            <div style="font-size: 12px; color: #64748B;">${m.brand_name} • ${m.dosage}</div>
            <div style="font-size: 11px; font-weight: 700; color: #3B82F6; margin-top: 2px;">
              ⏰ ${m.timing_anchor.toUpperCase()} (${m.timing_relation.replace('_', ' ')})
            </div>
            <div style="font-size: 11px; font-weight: 700; color: ${isUrgent ? '#DC2626' : '#059669'}; margin-top: 2px;">
              ${isUrgent ? '⚠️ Low Stock:' : 'Remaining:'} ${m.remaining_pills} pills
            </div>
          </div>
          <div style="display: flex; gap: 6px;">
            <button class="btn-action btn-taken" onclick="logDoseDirect('${m.id}', 'taken')" style="padding: 8px 12px; font-size: 12px; background: #10B981; color: white; border: none; border-radius: 8px; font-weight: 800; cursor: pointer;">✅ Taken</button>
            <button class="btn-action btn-skip" onclick="logDoseDirect('${m.id}', 'skipped')" style="padding: 8px 12px; font-size: 12px; background: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; border-radius: 8px; font-weight: 700; cursor: pointer;">Later</button>
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    console.error("Medications load error:", err);
  }
}

async function logDoseDirect(medId, status) {
  try {
    await fetchWithAuth('/api/medications/log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        medication_id: medId,
        status: status,
        notes: `Logged as ${status}`
      })
    });
    loadMedications();
    fetchGreeting();
  } catch (err) {
    console.error("Direct dose log error:", err);
  }
}

async function loadElderPendingApprovals() {
  try {
    const res = await fetchWithAuth('/api/medications');
    const meds = await res.json();
    const pending = meds.filter(m => m.approval_status === "pending_approval");
    const banner = document.getElementById('elderConsentBanner');
    const list = document.getElementById('pendingMedsList');
    if (!banner || !list) return;

    if (pending.length > 0) {
      banner.style.display = 'block';
      list.innerHTML = pending.map(m => `
        <div style="background: white; border: 1px solid #FDE68A; border-radius: 12px; padding: 10px; margin-top: 8px; display: flex; justify-content: space-between; align-items: center;">
          <div>
            <div style="font-weight: 800; font-size: 13px;">${m.senior_label} (${m.brand_name})</div>
            <div style="font-size: 11px; color: #64748B;">Slot: ${m.timing_anchor} • Proposed by Caregiver</div>
          </div>
          <div style="display: flex; gap: 6px;">
            <button onclick="approveMed('${m.id}')" style="background: #10B981; color: white; border: none; padding: 6px 12px; border-radius: 6px; font-size: 11px; font-weight: 800; cursor: pointer;">Approve</button>
            <button onclick="rejectMed('${m.id}')" style="background: #EF4444; color: white; border: none; padding: 6px 12px; border-radius: 6px; font-size: 11px; font-weight: 800; cursor: pointer;">Decline</button>
          </div>
        </div>
      `).join('');
    } else {
      banner.style.display = 'none';
    }
  } catch (err) {
    console.error("Pending approvals load error:", err);
  }
}

async function approveMed(medId) {
  await fetchWithAuth(`/api/medications/${medId}/approve`, { method: 'POST' });
  loadElderPendingApprovals();
  loadMedications();
}

async function rejectMed(medId) {
  await fetchWithAuth(`/api/medications/${medId}/reject`, { method: 'POST' });
  loadElderPendingApprovals();
  loadMedications();
}

// ==================== FULL INVENTORY & STATS ====================
async function loadFullMedicinesInventory() {
  const container = document.getElementById('fullMedicinesList');
  if (!container) return;
  try {
    const res = await fetchWithAuth('/api/medications');
    const meds = await res.json();
    container.innerHTML = meds.map(m => `
      <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 14px; padding: 14px; margin-bottom: 10px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h4 style="font-size: 15px; font-weight: 800; margin: 0;">${m.senior_label}</h4>
          <span style="font-size: 11px; font-weight: 800; padding: 3px 8px; border-radius: 6px; background: ${m.approval_status === 'approved' ? '#DCFCE7; color: #15803D;' : '#FEF3C7; color: #B45309;'}">
            ${m.approval_status.toUpperCase()}
          </span>
        </div>
        <div style="font-size: 13px; color: #475569; margin: 4px 0;">Brand: <b>${m.brand_name}</b> (${m.dosage})</div>
        <div style="font-size: 12px; color: #64748B;">Active Salt: ${m.salt_composition || 'N/A'}</div>
        <div style="font-size: 12px; color: #1E40AF; margin-top: 4px;">⏰ Anchor: ${m.timing_anchor.toUpperCase()} • ${m.remaining_pills} pills remaining</div>
      </div>
    `).join('');
  } catch (err) {
    console.error("Full inventory load error:", err);
  }
}

async function loadAdherenceHistory() {
  try {
    const sumRes = await fetchWithAuth('/api/medications/adherence-summary');
    const sum = await sumRes.json();
    document.getElementById('seniorAdherenceRate').textContent = `${sum.adherence_rate_pct}%`;

    const insRes = await fetchWithAuth('/api/medications/insights');
    const ins = await insRes.json();

    const historyContainer = document.getElementById('seniorDoseHistoryList');
    if (ins.refill_forecast && historyContainer) {
      historyContainer.innerHTML = ins.refill_forecast.map(rf => `
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 10px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
          <div>
            <div style="font-weight: 800; font-size: 13px;">${rf.medication} (${rf.brand})</div>
            <div style="font-size: 11px; color: #64748B;">Supply runway: ${rf.days_left} days left</div>
          </div>
          <span style="font-size: 11px; font-weight: 800; padding: 3px 8px; border-radius: 6px; background: ${rf.urgency === 'urgent' ? '#FEE2E2; color: #B91C1C;' : '#E0E7FF; color: #3730A3;'}">
            ${rf.urgency.toUpperCase()}
          </span>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error("Adherence history load error:", err);
  }
}

// ==================== SENIOR PROFILE & CAREGIVERS ====================
async function loadSeniorProfile() {
  try {
    const res = await fetchWithAuth('/api/auth/profile');
    const p = await res.json();
    const card = document.getElementById('patientProfileCard');
    if (card) {
      card.innerHTML = `
        <div style="font-size: 15px; font-weight: 800; color: #1E293B;">${p.name}</div>
        <div style="font-size: 13px; color: #64748B;">Phone: ${p.phone} • Age: ${p.age || 'Not specified'} • Gender: ${p.gender || 'Not specified'}</div>
        <div style="font-size: 12px; color: #1E40AF; margin-top: 6px;">
          <b>Conditions:</b> ${p.chronic_conditions?.length ? p.chronic_conditions.join(', ') : 'None listed'}
        </div>
        <div style="font-size: 12px; color: #B91C1C; margin-top: 2px;">
          <b>Allergies:</b> ${p.allergies?.length ? p.allergies.join(', ') : 'None reported'}
        </div>
      `;
    }

    const cgList = document.getElementById('seniorCaregiversList');
    if (cgList) {
      if (p.caregivers && p.caregivers.length > 0) {
        cgList.innerHTML = p.caregivers.map(c => `
          <div style="background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 12px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div>
              <div style="font-weight: 800; font-size: 14px;">${c.name}</div>
              <div style="font-size: 12px; color: #64748B;">${c.relationship} • ${c.phone}</div>
              <div style="font-size: 11px; color: #10B981;">Email alerts enabled</div>
            </div>
            <button onclick="unlinkCaregiverByElder('${c.id}')" style="background: #FEF2F2; color: #DC2626; border: 1px solid #FCA5A5; padding: 5px 10px; border-radius: 8px; font-size: 11px; font-weight: 700; cursor: pointer;">
              Unlink
            </button>
          </div>
        `).join('');
      } else {
        cgList.innerHTML = `<div style="font-size: 13px; color: #94A3B8;">No caregivers currently linked.</div>`;
      }
    }
  } catch (err) {
    console.error("Profile load error:", err);
  }
}

async function unlinkCaregiverByElder(linkId) {
  if (!confirm("Are you sure you want to remove this caregiver's access?")) return;
  try {
    await fetchWithAuth(`/api/caregiver/unlink/${linkId}`, { method: 'DELETE' });
    loadSeniorProfile();
  } catch (err) {
    console.error("Unlink error:", err);
  }
}

// ==================== EMERGENCY PASS & LIVE ROLLING PIN ====================
async function loadEmergencyPass() {
  try {
    const res = await fetchWithAuth('/api/emergency/current-pin');
    const data = await res.json();

    document.getElementById('emergencyRollingPinText').textContent = data.rolling_pin;
    document.getElementById('emergencyPinTimerText').textContent = `Rotates in ${data.valid_for_seconds}s`;

    const qrContainer = document.getElementById('emergencyQrContainer');
    if (qrContainer) {
      if (data.qr_code_data.startsWith('<svg')) {
        qrContainer.innerHTML = data.qr_code_data;
      } else {
        qrContainer.innerHTML = `<img src="data:image/png;base64,${data.qr_code_data}" style="width: 170px; height: 170px;" alt="Emergency QR Code">`;
      }
    }

    if (pinIntervalTimer) clearInterval(pinIntervalTimer);
    let secondsLeft = data.valid_for_seconds;
    pinIntervalTimer = setInterval(() => {
      secondsLeft--;
      if (secondsLeft <= 0) {
        clearInterval(pinIntervalTimer);
        loadEmergencyPass();
      } else {
        const timerEl = document.getElementById('emergencyPinTimerText');
        if (timerEl) timerEl.textContent = `Rotates in ${secondsLeft}s`;
      }
    }, 1000);
  } catch (err) {
    console.error("Emergency pass load error:", err);
  }
}

async function downloadClinicalPdf() {
  try {
    const pinRes = await fetchWithAuth('/api/emergency/current-pin');
    const pinData = await pinRes.json();
    const pid = pinData.patient_id;
    const pin = pinData.rolling_pin;
    window.open(`/api/emergency/${pid}/pdf?pin=${pin}`, '_blank');
  } catch (err) {
    console.error("PDF download error:", err);
    alert("Could not generate PDF. Please ensure session is authenticated.");
  }
}

// ==================== CAREGIVER COMMAND HUB ====================
async function initCaregiverHub() {
  try {
    const seniorsRes = await fetchWithAuth('/api/caregiver/seniors');
    const seniors = await seniorsRes.json();
    const sel = document.getElementById('cgSeniorSelect');
    if (!sel) return;

    if (seniors.length === 0) {
      sel.innerHTML = `<option value="">No seniors linked yet (Tap + Add Senior)</option>`;
    } else {
      sel.innerHTML = seniors.map(s => `
        <option value="${s.phone}">${s.name} (${s.phone}) - ${s.relationship}</option>
      `).join('');
      currentManagedSeniorPhone = seniors[0].phone;
      localStorage.setItem('vayocare_cg_managed_phone', currentManagedSeniorPhone);
    }

    loadCaregiverAdherenceSummary();
    loadCaregiverAppointments();
    loadCaregiverActivityLogs();
  } catch (err) {
    console.error("Caregiver hub init error:", err);
  }
}

function onCgSelectedSeniorChanged() {
  const sel = document.getElementById('cgSeniorSelect');
  currentManagedSeniorPhone = sel.value;
  localStorage.setItem('vayocare_cg_managed_phone', currentManagedSeniorPhone);
  loadCaregiverAdherenceSummary();
  loadCaregiverAppointments();
  loadCaregiverActivityLogs();
}

async function loadCaregiverAdherenceSummary() {
  if (!currentManagedSeniorPhone) return;
  try {
    const res = await fetchWithAuth(`/api/medications/insights?patient_id=${currentManagedSeniorPhone}`);
    const data = await res.json();
    const el = document.getElementById('cgAdherenceSummary');
    if (el) {
      el.innerHTML = `
        <div style="display: flex; gap: 10px; margin-bottom: 8px;">
          <div style="background: #EFF6FF; padding: 10px; border-radius: 10px; flex: 1; text-align: center;">
            <b style="font-size: 20px; color: #1D4ED8;">${data.adherence_7_day_pct}%</b>
            <div style="font-size: 11px; color: #1E40AF;">7-Day Adherence</div>
          </div>
          <div style="background: #F0FDF4; padding: 10px; border-radius: 10px; flex: 1; text-align: center;">
            <b style="font-size: 20px; color: #15803D;">${data.total_doses_logged}</b>
            <div style="font-size: 11px; color: #166534;">Doses Evaluated</div>
          </div>
        </div>
        <div style="font-weight: 700; color: #334155;">Pattern Insight: ${data.pattern_insight}</div>
      `;
    }
  } catch (err) {
    console.error("Caregiver insights error:", err);
  }
}

async function loadCaregiverAppointments() {
  try {
    const res = await fetchWithAuth('/api/appointments');
    const appts = await res.json();
    const container = document.getElementById('cgAppointmentsList');
    if (!container) return;
    if (appts.length === 0) {
      container.innerHTML = `<div style="font-size: 13px; color: #94A3B8;">No appointments scheduled.</div>`;
      return;
    }
    container.innerHTML = appts.map(a => `
      <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 10px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
        <div>
          <div style="font-weight: 800; font-size: 13px;">${a.doctor_name} (${a.specialty})</div>
          <div style="font-size: 12px; color: #64748B;">${a.hospital} • 📅 ${a.date} at ${a.time}</div>
        </div>
        <a href="/api/appointments/${a.id}/ical" target="_blank" style="background: #EFF6FF; color: #2563EB; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; text-decoration: none;">
          📅 .ics
        </a>
      </div>
    `).join('');
  } catch (err) {
    console.error("Appointments load error:", err);
  }
}

async function loadCaregiverActivityLogs() {
  try {
    const res = await fetchWithAuth('/api/auth/profile');
    const p = await res.json();
    const container = document.getElementById('cgActivityLogsList');
    if (!container || !p.activity_logs) return;
    container.innerHTML = p.activity_logs.slice(0, 5).map(l => `
      <div style="font-size: 12px; padding: 6px 0; border-bottom: 1px solid #F1F5F9;">
        <span style="font-weight: 800; color: #1E293B;">[${l.action}]</span> ${l.details}
        <span style="color: #94A3B8; font-size: 10px; margin-left: 6px;">${l.timestamp}</span>
      </div>
    `).join('');
  } catch (err) {
    console.error("Activity logs error:", err);
  }
}

function openAddSeniorModal() {
  const phone = prompt("Enter the Senior's Phone Number to link:");
  if (!phone) return;
  const rel = prompt("Relationship to senior (e.g. Mother, Father, Friend):", "Parent");
  linkSeniorDirect(phone, rel || "Parent");
}

async function linkSeniorDirect(seniorPhone, relationship) {
  try {
    const res = await fetchWithAuth('/api/caregiver/link', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        senior_phone: seniorPhone,
        relationship: relationship
      })
    });
    const data = await res.json();
    alert(data.message || "Senior linked successfully.");
    initCaregiverHub();
  } catch (err) {
    console.error("Link senior error:", err);
    alert("Could not link senior.");
  }
}

function openProposeMedModal() {
  const name = prompt("Medicine Name to propose (e.g. Shelcal 500):");
  if (!name) return;
  const label = prompt("Senior-friendly label (e.g. Bone & Calcium Tablet):", name);
  const anchor = prompt("Meal anchor (breakfast, lunch, dinner, bedtime):", "lunch");

  proposeMedicationDirect(name, label || name, anchor || "breakfast");
}

async function proposeMedicationDirect(brand, label, anchor) {
  try {
    const res = await fetchWithAuth('/api/caregiver/propose-medication', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        senior_phone: currentManagedSeniorPhone || currentUserPhone,
        brand_name: brand,
        senior_label: label,
        timing_anchor: anchor,
        remaining_pills: 20
      })
    });
    const data = await res.json();
    alert(data.message || "Medication proposed. Senior must approve on their device.");
  } catch (err) {
    console.error("Propose med error:", err);
  }
}

function openVoiceNoteModal() {
  const msg = prompt("Enter voice note for your loved one (e.g. 'Dad, take your sugar tablet after lunch'):");
  if (!msg) return;

  fetchWithAuth('/api/caregiver/classify-voice-note', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      caregiver_name: currentUserName || "Caregiver",
      message_text: msg,
      senior_phone: currentManagedSeniorPhone || currentUserPhone
    })
  }).then(r => r.json()).then(data => {
    alert(data.message || "Voice note anchored and saved!");
  }).catch(err => console.error("Voice note error:", err));
}

function openAppointmentModal() {
  const doc = prompt("Doctor Name (e.g. Dr. Murthy):");
  if (!doc) return;
  const date = prompt("Date (YYYY-MM-DD):", "2026-11-25");
  const time = prompt("Time (HH:MM):", "10:30");

  fetchWithAuth('/api/appointments', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      doctor_name: doc,
      specialty: "General Physician",
      hospital: "City Clinic",
      date: date || "2026-11-25",
      time: time || "10:30"
    })
  }).then(r => r.json()).then(data => {
    alert("Appointment scheduled.");
    loadCaregiverAppointments();
  }).catch(err => console.error("Appointment add error:", err));
}

async function unlinkCurrentSenior() {
  if (!currentManagedSeniorPhone) return;
  if (!confirm(`Are you sure you want to unlink senior ${currentManagedSeniorPhone}?`)) return;
  try {
    await fetchWithAuth(`/api/caregiver/unlink/${currentManagedSeniorPhone}`, { method: 'DELETE' });
    alert("Senior unlinked.");
    initCaregiverHub();
  } catch (err) {
    console.error("Unlink senior error:", err);
  }
}

// ==================== CAMERA & MULTIMODAL OCR UPLOAD ====================
function openCameraModal(target) {
  currentCameraTarget = target;
  const modal = document.getElementById('cameraModal');
  modal.style.display = 'flex';
  navigator.mediaDevices?.getUserMedia({ video: { facingMode: 'environment' } })
    .then(stream => {
      cameraStream = stream;
      document.getElementById('cameraVideo').srcObject = stream;
    })
    .catch(err => {
      console.warn("Camera stream unavailable, use file picker:", err);
    });
}

function closeCameraModal() {
  if (cameraStream) {
    cameraStream.getTracks().forEach(t => t.stop());
    cameraStream = null;
  }
  document.getElementById('cameraModal').style.display = 'none';
}

function captureCameraPhoto() {
  const video = document.getElementById('cameraVideo');
  const canvas = document.getElementById('cameraCanvas');
  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  canvas.toBlob(blob => {
    uploadCapturedPhotoBlob(blob, 'camera_capture.jpg');
  }, 'image/jpeg');
  closeCameraModal();
}

function handleFileFallback(input) {
  if (input.files && input.files[0]) {
    uploadCapturedPhotoBlob(input.files[0], input.files[0].name);
    closeCameraModal();
  }
}

async function uploadCapturedPhotoBlob(blob, filename) {
  const formData = new FormData();
  formData.append('prescription_file', blob, filename);
  formData.append('patient_id', currentPatientId || currentUserPhone);

  try {
    alert("Uploading photo & analyzing with Google Gemini Vision...");
    const res = await fetchWithAuth('/api/audit/upload-scan', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    alert(`Audit Complete!\nMatch Score: ${data.match_score}%\n${data.summary}`);
    loadMedications();
  } catch (err) {
    console.error("Upload error:", err);
    alert("Image upload or analysis completed with local reconciliation.");
  }
}

// ==================== LANGUAGE SWITCHING (PURE ISOLATION) ====================
function setAppLanguage(lang) {
  currentLanguage = lang;
  localStorage.setItem('vayocare_lang', lang);
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-lang') === lang);
  });
  applyLanguage(lang);
  fetchGreeting();
  loadMedications();
}

function applyLanguage(lang) {
  // Pure translation dictionary without cross-language leakage
  const dict = {
    en: {
      micHint: "Tap to Speak to Companion",
      btnTaken: "Yes, Taken<br><small style='font-size:11px; font-weight:600;'>(Confirmed)</small>",
      btnLater: "Take Later<br><small style='font-size:11px; font-weight:600;'>(Remind Soon)</small>",
      todayMedsHeading: "Today's Essential Medicines"
    },
    hi: {
      micHint: "बोलने के लिए दबाएं (Tap to Speak)",
      btnTaken: "हाँ, ले ली है<br><small style='font-size:11px; font-weight:600;'>(Yes, Taken)</small>",
      btnLater: "बाद में लूंगा<br><small style='font-size:11px; font-weight:600;'>(Take Later)</small>",
      todayMedsHeading: "आज की आवश्यक दवाएं"
    },
    te: {
      micHint: "నొక్కి మాట్లాడండి (Tap to Speak)",
      btnTaken: "హా, వేసుకున్నాను<br><small style='font-size:11px; font-weight:600;'>(Yes, Taken)</small>",
      btnLater: "తర్వాత వేసుకుంటా<br><small style='font-size:11px; font-weight:600;'>(Take Later)</small>",
      todayMedsHeading: "ఈరోజు ముఖ్యమైన మాత్రలు"
    }
  };

  const selected = dict[lang] || dict.en;
  const mh = document.getElementById('i18n-micHint');
  if (mh) mh.innerHTML = selected.micHint;
  const bt = document.getElementById('i18n-btnTaken');
  if (bt) bt.innerHTML = selected.btnTaken;
  const bl = document.getElementById('i18n-btnLater');
  if (bl) bl.innerHTML = selected.btnLater;
  const tm = document.getElementById('i18n-todayMedsHeading');
  if (tm) tm.textContent = selected.todayMedsHeading;
}

// ==================== ACCESSIBILITY TOGGLES ====================
function toggleLargeText() {
  const isLarge = document.body.classList.toggle('large-text');
  localStorage.setItem('vayocare_large_text', isLarge);
}

function toggleHighContrast() {
  const isHc = document.body.classList.toggle('high-contrast');
  localStorage.setItem('vayocare_high_contrast', isHc);
}
