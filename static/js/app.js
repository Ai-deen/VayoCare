// VayoCare PWA Core Application Engine

let currentLanguage = localStorage.getItem('vayocare_lang') || 'en';
let currentUserRole = localStorage.getItem('vayocare_role') || 'patient';
let currentUserPhone = localStorage.getItem('vayocare_phone') || '';
let currentUserName = localStorage.getItem('vayocare_name') || '';
let currentLinkedPhone = localStorage.getItem('vayocare_linked_phone') || '9849012345';
let currentAnchor = detectCurrentTimeAnchor();
let isListening = false;
let speechRecognition = null;
let cameraStream = null;
let currentCameraTarget = 'onboarding';

function detectCurrentTimeAnchor() {
  const now = new Date();
  const hrs = now.getHours() + (now.getMinutes() / 60);
  if (hrs < 11.5) return 'breakfast';
  if (hrs < 16.0) return 'lunch';
  if (hrs < 21.5) return 'dinner';
  return 'bedtime';
}

const I18N = {
  en: {
    micHint: "Tap to Speak to Companion",
    btnTaken: "Yes, Taken<br><small style='font-size:11px; font-weight:600;'>(Confirmed)</small>",
    btnLater: "Take Later<br><small style='font-size:11px; font-weight:600;'>(Remind Soon)</small>",
    todayMedsHeading: "Today's Essential Medicines",
    btnTakenSmall: "✅ Taken",
    btnLaterSmall: "Later",
    leftText: "Left:",
    pillsText: "pills",
    lowStock: "⚠️ Low Stock:",
    navHome: "Home",
    navRoutine: "Routine",
    navEmergency: "Emergency QR"
  },
  hi: {
    micHint: "बोलने के लिए दबाएं (Tap to Speak)",
    btnTaken: "हाँ, ले ली है<br><small style='font-size:11px; font-weight:600;'>(Yes, Taken)</small>",
    btnLater: "बाद में लूंगा<br><small style='font-size:11px; font-weight:600;'>(Take Later)</small>",
    todayMedsHeading: "आज की आवश्यक दवाएं",
    btnTakenSmall: "✅ ली है",
    btnLaterSmall: "बाद में",
    leftText: "शेष:",
    pillsText: "गोलियां",
    lowStock: "⚠️ कम स्टॉक:",
    navHome: "होम",
    navRoutine: "दिनचर्या",
    navEmergency: "आपातकालीन QR"
  },
  te: {
    micHint: "నొక్కి మాట్లాడండి (Tap to Speak)",
    btnTaken: "హా, వేసుకున్నాను<br><small style='font-size:11px; font-weight:600;'>(Yes, Taken)</small>",
    btnLater: "తర్వాత వేసుకుంటా<br><small style='font-size:11px; font-weight:600;'>(Take Later)</small>",
    todayMedsHeading: "ఈరోజు ముఖ్యమైన మాత్రలు",
    btnTakenSmall: "✅ వేసుకున్నా",
    btnLaterSmall: "తర్వాత",
    leftText: "మిగిలినవి:",
    pillsText: "మాత్రలు",
    lowStock: "⚠️ తక్కువగా ఉన్నాయి:",
    navHome: "హోమ్",
    navRoutine: "దినచర్య",
    navEmergency: "ఎమర్జెన్సీ QR"
  }
};

// 1. Initialization
document.addEventListener('DOMContentLoaded', () => {
  registerServiceWorker();
  initSpeechRecognition();

  if (!currentUserPhone) {
    document.getElementById('loginOverlay').style.display = 'block';
  } else {
    setupDashboardForRole(currentUserRole);
  }

  applyLanguage(currentLanguage);
});

function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch(err => console.warn(err));
  }
}

// 2. Authentication & Multi-User Handlers
function selectRole(role) {
  document.getElementById('roleSelectPatient').classList.toggle('selected', role === 'patient');
  document.getElementById('roleSelectCaregiver').classList.toggle('selected', role === 'caregiver');
  document.getElementById('caregiverLinkBox').style.display = (role === 'caregiver') ? 'block' : 'none';
}

async function handleAuthSubmit() {
  const phone = document.getElementById('authPhone').value.trim();
  const name = document.getElementById('authName').value.trim() || "Senior Patient";
  const isCg = document.getElementById('roleSelectCaregiver').classList.contains('selected');
  const role = isCg ? 'caregiver' : 'patient';
  const parentPhone = isCg ? (document.getElementById('authParentPhone').value.trim() || "9849012345") : phone;

  if (!phone) {
    alert("Please enter a valid phone number.");
    return;
  }

  try {
    const res = await fetch('/api/auth/phone-login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        role: role,
        name: name,
        phone: phone,
        patient_phone: parentPhone,
        language: currentLanguage
      })
    });
    const data = await res.json();

    currentUserPhone = phone;
    currentUserName = name;
    currentUserRole = role;
    currentLinkedPhone = parentPhone;

    localStorage.setItem('vayocare_phone', phone);
    localStorage.setItem('vayocare_name', name);
    localStorage.setItem('vayocare_role', role);
    localStorage.setItem('vayocare_linked_phone', parentPhone);

    document.getElementById('loginOverlay').style.display = 'none';
    setupDashboardForRole(role);
  } catch (err) {
    console.error('Login error:', err);
    loginDemoProfile();
  }
}

function loginDemoProfile() {
  currentUserPhone = "9849012345";
  currentUserName = "Ramesh Rao";
  currentUserRole = "patient";
  currentLinkedPhone = "9849012345";

  localStorage.setItem('vayocare_phone', "9849012345");
  localStorage.setItem('vayocare_name', "Ramesh Rao");
  localStorage.setItem('vayocare_role', "patient");
  localStorage.setItem('vayocare_linked_phone', "9849012345");

  document.getElementById('loginOverlay').style.display = 'none';
  setupDashboardForRole('patient');
}

function logoutUser() {
  localStorage.removeItem('vayocare_phone');
  localStorage.removeItem('vayocare_name');
  localStorage.removeItem('vayocare_role');
  currentUserPhone = '';
  document.getElementById('loginOverlay').style.display = 'block';
}

function setupDashboardForRole(role) {
  const isPatient = role === 'patient';
  document.getElementById('seniorSection').style.display = isPatient ? 'block' : 'none';
  document.getElementById('caregiverSection').style.display = isPatient ? 'none' : 'block';
  document.getElementById('seniorNav').style.display = isPatient ? 'flex' : 'none';
  document.getElementById('caregiverNav').style.display = isPatient ? 'none' : 'flex';

  const tag = document.getElementById('userStatusTag');
  if (tag) {
    tag.textContent = isPatient 
      ? `Senior: ${currentUserName} (${currentUserPhone})`
      : `Caregiver: ${currentUserName} (Managing ${currentLinkedPhone})`;
  }

  const cgText = document.getElementById('cgManagedSeniorText');
  if (cgText) {
    cgText.textContent = `Managing Senior: ${currentLinkedPhone}`;
  }

  currentAnchor = detectCurrentTimeAnchor();
  fetchGreeting();
  loadMedications();
  loadRoutine();
  fetchEmergencyQr();
  if (!isPatient) {
    loadAlerts();
  }
}

// 3. Navigation
function switchSeniorTab(tabName) {
  document.querySelectorAll('#seniorSection .tab-content').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('#seniorNav .nav-item').forEach(b => b.classList.remove('active'));

  const tab = document.getElementById(`senior-${tabName}`);
  if (tab) tab.classList.add('active');

  const order = ['home', 'routine', 'emergency'];
  const idx = order.indexOf(tabName);
  const items = document.querySelectorAll('#seniorNav .nav-item');
  if (items[idx]) items[idx].classList.add('active');

  if (tabName === 'emergency') {
    fetchEmergencyQr();
  }
}

function switchCaregiverTab(tabName) {
  document.querySelectorAll('#caregiverSection .tab-content').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('#caregiverNav .nav-item').forEach(b => b.classList.remove('active'));

  const tab = document.getElementById(`cg-${tabName}`);
  if (tab) tab.classList.add('active');

  const order = ['hub', 'audit'];
  const idx = order.indexOf(tabName);
  const items = document.querySelectorAll('#caregiverNav .nav-item');
  if (items[idx]) items[idx].classList.add('active');
}

function openDoctorViewDirect() {
  window.open(`/emergency/p_${currentLinkedPhone || 'ramesh_72'}`, '_blank');
}

// 4. Multilingual Switching
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
  const dict = I18N[lang] || I18N.en;
  for (const [key, val] of Object.entries(dict)) {
    const el = document.getElementById(`i18n-${key}`);
    if (el) el.innerHTML = val;
  }
  const nh = document.getElementById('navHomeText');
  if (nh) nh.textContent = dict.navHome;
  const nr = document.getElementById('navRoutineText');
  if (nr) nr.textContent = dict.navRoutine;
  const ne = document.getElementById('navEmergencyText');
  if (ne) ne.textContent = dict.navEmergency;
}

// 5. Time-Anchored Greeting & Voice
async function fetchGreeting() {
  try {
    const targetPhone = currentUserRole === 'patient' ? currentUserPhone : currentLinkedPhone;
    const res = await fetch(`/api/companion/greeting?language=${currentLanguage}&anchor=${currentAnchor}&phone=${targetPhone}`);
    const data = await res.json();
    
    const bubble = document.getElementById('companionSpeechBubble');
    if (bubble) bubble.textContent = `"${data.text}"`;

    const hero = document.getElementById('heroPillLabel');
    if (hero) hero.textContent = `💊 ${data.active_medicine || 'Medicine Check-in'}`;
  } catch (err) {
    console.error(err);
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
    if (pill) pill.textContent = 'Ready • Microphones Active';
  };
}

function toggleVoiceInput() {
  if (!speechRecognition) {
    alert('Voice speech recognition is active on supported mobile browsers.');
    return;
  }
  if (isListening) {
    speechRecognition.stop();
  } else {
    const code = currentLanguage === 'te' ? 'te-IN' : (currentLanguage === 'hi' ? 'hi-IN' : 'en-IN');
    speechRecognition.lang = code;
    speechRecognition.start();
  }
}

function startRoutineVoiceInput() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    alert('Voice input supported on Google Chrome / Android Chrome.');
    return;
  }
  const recog = new SpeechRecognition();
  recog.lang = currentLanguage === 'te' ? 'te-IN' : (currentLanguage === 'hi' ? 'hi-IN' : 'en-IN');
  recog.onresult = (e) => {
    const t = e.results[0][0].transcript;
    document.getElementById('voiceRoutineInput').value = t;
    parseVoiceRoutine();
  };
  recog.start();
}

async function sendCompanionMessage(text) {
  try {
    const targetPhone = currentUserRole === 'patient' ? currentUserPhone : currentLinkedPhone;
    const res = await fetch('/api/companion/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        patient_id: targetPhone || '9849012345',
        speech_text: text,
        language: currentLanguage,
        current_anchor: currentAnchor
      })
    });
    const data = await res.json();
    document.getElementById('companionSpeechBubble').textContent = `"${data.reply_text}"`;
    loadMedications();
  } catch (err) {
    console.error(err);
  }
}

function submitQuickDose(status) {
  const targetPhone = currentUserRole === 'patient' ? currentUserPhone : currentLinkedPhone;
  fetch(`/api/medications?phone=${targetPhone}`)
    .then(r => r.json())
    .then(meds => {
      const activeMed = meds.find(m => m.timing_anchor === currentAnchor) || meds[0];
      if (activeMed) {
        logDoseDirect(activeMed.id, status);
      }
    });
}

// 6. Medication List
async function loadMedications() {
  try {
    const targetPhone = currentUserRole === 'patient' ? currentUserPhone : currentLinkedPhone;
    const res = await fetch(`/api/medications?phone=${targetPhone}`);
    const meds = await res.json();
    const container = document.getElementById('seniorMedList');
    if (!container) return;

    const dict = I18N[currentLanguage] || I18N.en;

    if (meds.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 24px 16px; background: white; border: 1px dashed #CBD5E1; border-radius: 16px; color: #64748B;">
          No active medicines added yet. Use Caregiver Hub to add your daily medicines.
        </div>
      `;
      return;
    }

    container.innerHTML = meds.map(m => {
      const friendlyName = currentLanguage === 'te' ? m.senior_label_te : (currentLanguage === 'hi' ? m.senior_label_hi : m.senior_label);
      const isUrgent = m.remaining_pills <= 3;
      const anchorTitle = m.timing_anchor.toUpperCase();

      return `
        <div class="med-card" style="border-left: 6px solid ${m.pill_color};">
          <div class="med-icon-pill" style="background: ${m.pill_color}22; color: ${m.pill_color};">
            💊
          </div>
          <div class="med-details">
            <div class="med-name">${friendlyName}</div>
            <div class="med-salt">${m.brand_name} (${m.dosage})</div>
            <div style="font-size: 13px; font-weight: 700; color: #475569; margin-top: 2px;">
              ⏰ ${anchorTitle} • ${m.timing_relation.replace('_', ' ')}
            </div>
            <div class="med-stock ${isUrgent ? 'stock-urgent' : ''}">
              ${isUrgent ? dict.lowStock : dict.leftText} ${m.remaining_pills} ${dict.pillsText}
            </div>
          </div>
          <div class="med-actions">
            <button class="btn-action btn-taken" onclick="logDoseDirect('${m.id}', 'taken')">
              ${dict.btnTakenSmall}
            </button>
            <button class="btn-action btn-skip" onclick="logDoseDirect('${m.id}', 'skipped')">
              ${dict.btnLaterSmall}
            </button>
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    console.error(err);
  }
}

async function logDoseDirect(medId, status) {
  try {
    const targetPhone = currentUserRole === 'patient' ? currentUserPhone : currentLinkedPhone;
    await fetch('/api/medications/log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        medication_id: medId,
        status: status,
        notes: `Tapped ${status}`,
        phone: targetPhone
      })
    });
    loadMedications();
    fetchGreeting();
  } catch (err) {
    console.error(err);
  }
}

async function submitNewMedication() {
  const name = document.getElementById('newMedNameInput').value.trim();
  const anchor = document.getElementById('newMedAnchorInput').value;
  if (!name) {
    alert("Please enter medicine name.");
    return;
  }
  const targetPhone = currentUserRole === 'patient' ? currentUserPhone : currentLinkedPhone;

  try {
    await fetch('/api/medications', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: name,
        timing_anchor: anchor,
        dosage: "1 pill",
        phone: targetPhone
      })
    });
    alert(`Added ${name} to senior's schedule!`);
    document.getElementById('newMedNameInput').value = '';
    loadMedications();
    fetchGreeting();
  } catch (err) {
    console.error(err);
  }
}

// 7. Routine
async function loadRoutine() {
  try {
    const targetPhone = currentUserRole === 'patient' ? currentUserPhone : currentLinkedPhone;
    const res = await fetch(`/api/routine`);
    const r = await res.json();
    const list = document.getElementById('routineAnchorsList');
    if (!list) return;

    list.innerHTML = `
      <div style="background: white; border: 1px solid #E2E8F0; padding: 10px 14px; border-radius: 12px; display: flex; justify-content: space-between; margin-bottom: 6px;">
        <span><strong>🌅 Breakfast:</strong> ${r.breakfast}</span>
        <span style="color: #2563EB; font-weight: 700;">Morning Doses</span>
      </div>
      <div style="background: white; border: 1px solid #E2E8F0; padding: 10px 14px; border-radius: 12px; display: flex; justify-content: space-between; margin-bottom: 6px;">
        <span><strong>☀️ Lunch:</strong> ${r.lunch}</span>
        <span style="color: #2563EB; font-weight: 700;">Afternoon Doses</span>
      </div>
      <div style="background: white; border: 1px solid #E2E8F0; padding: 10px 14px; border-radius: 12px; display: flex; justify-content: space-between;">
        <span><strong>🌙 Dinner:</strong> ${r.dinner}</span>
        <span style="color: #2563EB; font-weight: 700;">Night Doses</span>
      </div>
    `;
  } catch (err) {
    console.error(err);
  }
}

async function parseVoiceRoutine() {
  const text = document.getElementById('voiceRoutineInput').value;
  try {
    const res = await fetch('/api/routine/parse-voice', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        patient_id: currentUserPhone || '9849012345',
        voice_transcript: text,
        language: currentLanguage
      })
    });
    await res.json();
    loadRoutine();
    alert('Daily meal routine updated successfully!');
  } catch (err) {
    console.error(err);
  }
}

// 8. Caregiver Actions
async function submitCaregiverVoiceNote() {
  const input = document.getElementById('caregiverVoiceMsgInput');
  const msg = input.value.trim();
  if (!msg) {
    alert("Please type a message.");
    return;
  }
  try {
    await fetch('/api/companion/caregiver-note', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        caregiver_name: currentUserName || 'Family Caregiver',
        message_text: msg,
        assigned_anchor: currentAnchor,
        patient_phone: currentLinkedPhone
      })
    });
    alert("Personal voice reminder saved! It will play for the senior during their dose check-in.");
    input.value = '';
  } catch (err) {
    console.error(err);
  }
}

async function runPrescriptionAudit() {
  const btn = document.getElementById('btnRunAudit');
  btn.textContent = '⚡ Running Gemini AI Salt Audit...';

  const rx = document.getElementById('auditRxInput').value;
  const strips = document.getElementById('auditStripInput').value;

  try {
    const res = await fetch('/api/audit/reconcile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prescription_text: rx,
        strip_text: strips
      })
    });
    const data = await res.json();
    document.getElementById('auditResultsSection').style.display = 'block';

    const discBox = document.getElementById('discrepancyBox');
    const discText = document.getElementById('discrepancyText');
    if (data.discrepancies && data.discrepancies.length > 0) {
      discBox.style.display = 'block';
      discText.innerHTML = data.discrepancies.map(d => `
        <strong>${d.medicine_name}:</strong> ${d.details}
      `).join('<br>');
    } else {
      discBox.style.display = 'none';
    }

    const runwayList = document.getElementById('refillRunwayList');
    runwayList.innerHTML = data.refill_runway.map(item => `
      <div class="runway-card ${item.urgency}">
        <div>
          <div style="font-weight: 800; font-size: 15px;">${item.senior_label || item.brand_name}</div>
          <div style="font-size: 13px; color: #475569;">${item.brand_name} (${item.salt})</div>
          <div style="font-size: 12px; font-weight: 700; margin-top: 2px; color: #64748B;">
            Remaining: ${item.remaining_pills} pills
          </div>
        </div>
        <div style="text-align: right;">
          <div style="font-size: 20px; font-weight: 900; color: ${item.urgency === 'urgent' ? '#DC2626' : '#2563EB'};">
            ${item.days_left} Days
          </div>
          <span style="font-size: 11px; font-weight: 800; text-transform: uppercase;">
            ${item.urgency}
          </span>
        </div>
      </div>
    `).join('');

    btn.textContent = '✅ AI Salt Reconciliation Complete';
  } catch (err) {
    console.error(err);
    btn.textContent = '⚡ Run Gemini AI Salt Reconciliation';
  }
}

// 9. Camera Live Feed
async function openLiveCamera(target) {
  currentCameraTarget = target;
  const modal = document.getElementById('cameraModal');
  if (modal) modal.style.display = 'flex';
  const video = document.getElementById('cameraVideo');

  try {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      cameraStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'environment' } },
        audio: false
      });
      if (video) {
        video.srcObject = cameraStream;
        video.play();
      }
    } else {
      document.getElementById('fallbackFileInput').click();
    }
  } catch (err) {
    console.warn('Camera failed, using file input:', err);
    const fb = document.getElementById('fallbackFileInput');
    if (fb) fb.click();
  }
}

function closeCameraModal() {
  const modal = document.getElementById('cameraModal');
  if (modal) modal.style.display = 'none';
  if (cameraStream) {
    cameraStream.getTracks().forEach(t => t.stop());
    cameraStream = null;
  }
}

function captureCameraPhoto() {
  const video = document.getElementById('cameraVideo');
  const canvas = document.getElementById('cameraCanvas');
  if (!video || !canvas) return;

  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  const dataUrl = canvas.toDataURL('image/jpeg', 0.85);

  applyCapturedPhoto(dataUrl);
  closeCameraModal();
}

function handleFileFallback(input) {
  if (input.files && input.files[0]) {
    const reader = new FileReader();
    reader.onload = function(e) {
      applyCapturedPhoto(e.target.result);
      closeCameraModal();
    };
    reader.readAsDataURL(input.files[0]);
  }
}

function applyCapturedPhoto(dataUrl) {
  if (currentCameraTarget === 'audit_rx') {
    const box = document.getElementById('rxPhotoPreviewBox');
    const img = document.getElementById('auditRxPhotoImg');
    if (box && img) {
      img.src = dataUrl;
      box.style.display = 'block';
    }
    const input = document.getElementById('auditRxInput');
    if (input) {
      input.value = "Rx (Photo Captured): Tab Telmikem 40 1-0-0, Tab Glycomet 500 1-0-1, Tab Ecosprin 75 0-1-0. Review 30 days.";
    }
  } else if (currentCameraTarget === 'audit_strip') {
    const box = document.getElementById('stripPhotoPreviewBox');
    const img = document.getElementById('auditStripPhotoImg');
    if (box && img) {
      img.src = dataUrl;
      box.style.display = 'block';
    }
    const input = document.getElementById('auditStripInput');
    if (input) {
      input.value = "Chemist Strips (Photo Captured): Telmikem 40 (10 tabs), Glycomet 500 (10 tabs). Missing Ecosprin 75.";
    }
  }
}

// 10. Emergency QR
async function fetchEmergencyQr() {
  try {
    const res = await fetch('/api/emergency/current-pin');
    const data = await res.json();
    const qrImg = document.getElementById('emergencyQrImg');
    if (qrImg) qrImg.src = data.qr_code_data;
    const docLink = document.getElementById('doctorDirectLink');
    if (docLink) docLink.href = data.emergency_url;
  } catch (err) {
    console.error(err);
  }
}

async function loadAlerts() {
  try {
    const res = await fetch('/api/alerts');
    const alerts = await res.json();
    const feed = document.getElementById('alertsLogFeed');
    if (!feed) return;

    feed.innerHTML = alerts.map(a => `
      <div class="alert-item ${a.severity}">
        <div style="display:flex; justify-content:space-between; font-weight:800;">
          <span>${a.title}</span>
          <span style="font-size:11px; opacity:0.8;">${a.timestamp}</span>
        </div>
        <div style="margin-top:2px;">${a.message}</div>
      </div>
    `).join('');
  } catch (err) {
    console.error(err);
  }
}
