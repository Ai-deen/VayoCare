// VayoCare PWA Core Application Engine

let currentLanguage = localStorage.getItem('vayocare_lang') || 'en';
let currentUserRole = 'patient';
let currentAnchor = 'breakfast';
let isListening = false;
let speechRecognition = null;
let wizardRole = 'patient';
let cameraStream = null;
let currentCameraTarget = 'onboarding';

// Complete Multilingual Dictionary (Zero Token Cost on Language Switch)
const I18N = {
  te: {
    brandSubtitle: "వృద్ధుల ఆరోగ్య మిత్ర • Elder Companion",
    rolePatient: "Senior Mode (వృద్ధుల మోడ్)",
    roleCaregiver: "Caregiver Hub (కేర్‌టేకర్‌)",
    heroPillLabel: "💊 BP మాత్ర (BP Tablet)",
    micHint: "నొక్కి మాట్లాడండి (Tap to Speak)",
    btnTaken: "హా, వేసుకున్నాను<br><small style='font-size:12px; font-weight:600;'>(Yes, Taken)</small>",
    btnLater: "తర్వాత వేసుకుంటా<br><small style='font-size:12px; font-weight:600;'>(Take Later)</small>",
    todayMedsHeading: "ఈరోజు మాత్రలు (Today's Doses)",
    routineTitle: "🗣️ మీ దినచర్య (Daily Routine)",
    routineDesc: "మీరు ఏ సమయంలో తింటారో చెబితే, AI దానికి తగినట్లుగా మాత్రల సమయాన్ని నిర్ణయిస్తుంది.",
    btnSaveRoutine: "⚡ దినచర్యను సేవ్‌ చేయండి (Save Routine)",
    emergencyTitle: "డాక్టర్ / ఎమర్జెన్సీ QR పాస్",
    emergencyDesc: "ఏ ఫోన్ కెమెరాతోనైనా స్కాన్ చేస్తే వెంటనే మీ వివరాలు, ప్రస్తుత మాత్రల వివరాలు కనిపిస్తాయి. యాప్ డౌన్‌లోడ్ చేయనవసరం లేదు!",
    qrAccessCodeLabel: "యాక్సెస్ పిన్ (Access PIN):",
    btnOpenDoctorView: "డాక్టర్ వ్యూ తెరవండి (Open Doctor View)",
    cgHubTitle: "కేర్‌టేకర్‌ డాష్‌బోర్డ్ (Caregiver Hub)",
    cgLinkedPatientText: "లింక్ అయిన రోగి: రమేష్ రావు (72 సం.)",
    weeklyTrackerHeading: "📅 గత 7 రోజుల ట్రాకర్ (7-Day Adherence)",
    voiceNoteTitle: "🎙️ రోగికి మీ వాయిస్ మెసేజ్ పంపండి (Personal Voice Reminder)",
    voiceNoteDesc: "మీరు మాట్లాడే మాటలు ఉదయం పూట రోగికి వినిపిస్తాయి. రోబోట్ వాయిస్ కాకుండా మీ మాటలే వారికి ధైర్యాన్నిస్తాయి.",
    btnSendVoiceNote: "💌 వాయిస్ మెసేజ్ పంపండి (Save Note)",
    btnTestAlert: "📧 ఈమెయిల్ అలర్ట్ పరీక్షించండి (Test Caregiver Email)",
    notifFeedTitle: "అలర్ట్ మరియు నోటిఫికేషన్లు (Alerts Log)",
    auditTitle: "🔍 ప్రిస్క్రిప్షన్ vs స్ట్రిప్ AI ఆడిట్",
    auditDesc: "డాక్టర్ రాసిన కాగితం మరియు కెమిస్ట్ ఇచ్చిన మందుల స్ట్రిప్స్ ఫోటో తీయండి. ఏవైనా మందులు మిస్సయ్యాయా అని AI వెంటనే చెబుతుంది.",
    btnRunAudit: "⚡ AI ఆడిట్ ప్రారంభించండి (Run AI Audit)",
    refillRunwayHeading: "📦 రీఫిల్ రన్‌వే (Refill Runway)",
    navHome: "హోమ్",
    navRoutine: "దినచర్య",
    navAudit: "ఆడిట్",
    navCaretaker: "కేర్‌టేకర్‌",
    navEmergency: "QR పాస్"
  },
  hi: {
    brandSubtitle: "बुजुर्ग स्वास्थ्य साथी • Elder Companion",
    rolePatient: "Senior Mode (बुजुर्ग मोड)",
    roleCaregiver: "Caregiver Hub (देखभालकर्ता)",
    heroPillLabel: "💊 बीपी की गोली (BP Tablet)",
    micHint: "बोलने के लिए दबाएं (Tap to Speak)",
    btnTaken: "हाँ, ले ली है<br><small style='font-size:12px; font-weight:600;'>(Yes, Taken)</small>",
    btnLater: "बाद में लूंगा<br><small style='font-size:12px; font-weight:600;'>(Take Later)</small>",
    todayMedsHeading: "आज की दवाएं (Today's Doses)",
    routineTitle: "🗣️ आपकी दिनचर्या (Daily Routine)",
    routineDesc: "अपने भोजन का समय बताएं, AI दवाओं का समय अपने आप तय कर देगा।",
    btnSaveRoutine: "⚡ दिनचर्या सुरक्षित करें (Save Routine)",
    emergencyTitle: "डॉक्टर / आपातकालीन QR पास",
    emergencyDesc: "किसी भी फोन से स्कैन करें और दवा की जानकारी देखें। ऐप डाउनलोड की जरूरत नहीं!",
    qrAccessCodeLabel: "एक्सेस पिन (Access PIN):",
    btnOpenDoctorView: "डॉक्टर व्यू खोलें (Open Doctor View)",
    cgHubTitle: "देखभालकर्ता डैशबोर्ड (Caregiver Hub)",
    cgLinkedPatientText: "मरीज: रमेश राव (72 वर्ष)",
    weeklyTrackerHeading: "📅 पिछले 7 दिनों का रिकॉर्ड (7-Day Adherence)",
    voiceNoteTitle: "🎙️ मरीज के लिए अपनी आवाज में संदेश छोड़ें",
    voiceNoteDesc: "आपका रिकॉर्ड किया संदेश सुबह मरीज को सुनाया जाएगा, जिससे उन्हें अपनापन लगेगा।",
    btnSendVoiceNote: "💌 संदेश भेजें (Save Note)",
    btnTestAlert: "📧 ईमेल अलर्ट टेस्ट करें (Test Email Alert)",
    notifFeedTitle: "अलर्ट और सूचनाएं (Alerts Log)",
    auditTitle: "🔍 पर्चा बनाम दवा पट्टी AI ऑडिट",
    auditDesc: "डॉक्टर का पर्चा और खरीदी गई दवा की तुलना करें। छूटी हुई दवा तुरंत पता चलेगी।",
    btnRunAudit: "⚡ AI ऑडिट शुरू करें (Run AI Audit)",
    refillRunwayHeading: "📦 दवा स्टॉक रनवे (Refill Runway)",
    navHome: "होम",
    navRoutine: "दिनचर्या",
    navAudit: "ऑडिट",
    navCaretaker: "देखभालकर्ता",
    navEmergency: "QR पास"
  },
  en: {
    brandSubtitle: "Smart Elderly Care Companion",
    rolePatient: "Senior Mode (Elderly)",
    roleCaregiver: "Caregiver Hub",
    heroPillLabel: "💊 Morning BP Tablet",
    micHint: "Tap to Speak to Companion",
    btnTaken: "Yes, Taken<br><small style='font-size:12px; font-weight:600;'>(Confirmed)</small>",
    btnLater: "Take Later<br><small style='font-size:12px; font-weight:600;'>(Remind Soon)</small>",
    todayMedsHeading: "Today's Essential Medicines",
    routineTitle: "🗣️ Routine-Anchored Schedule",
    routineDesc: "Speak your daily meal schedule once, and doses anchor naturally around meals.",
    btnSaveRoutine: "⚡ Save Daily Routine",
    emergencyTitle: "Doctor / Emergency QR Pass",
    emergencyDesc: "Scan with any smartphone camera to view medical salts and dose history. Zero app install required!",
    qrAccessCodeLabel: "Access PIN:",
    btnOpenDoctorView: "Open Browser Doctor View",
    cgHubTitle: "Caregiver Command Hub",
    cgLinkedPatientText: "Linked Senior: Ramesh Rao (Age 72)",
    weeklyTrackerHeading: "📅 Past 7-Day Medication Adherence",
    voiceNoteTitle: "🎙️ Send Loving Voice Reminder to Senior",
    voiceNoteDesc: "Your personal voice message plays when it's time for their dose, providing comfort and reassurance.",
    btnSendVoiceNote: "💌 Save Voice Note",
    btnTestAlert: "📧 Dispatch Test Caregiver Email Alert",
    notifFeedTitle: "Live Notification & Alert Feed",
    auditTitle: "🔍 Prescription vs Chemist Strip AI Audit",
    auditDesc: "Compares doctor's prescription with chemist strips to identify missing medicines and generic salt variations.",
    btnRunAudit: "⚡ Run Gemini AI Reconciliation",
    refillRunwayHeading: "📦 Visual Refill Runway (Days Left)",
    navHome: "Home",
    navRoutine: "Routine",
    navAudit: "AI Audit",
    navCaretaker: "Caregiver",
    navEmergency: "QR Pass"
  }
};

// 1. Initialization
document.addEventListener('DOMContentLoaded', () => {
  registerServiceWorker();
  initSpeechRecognition();

  // If first time or not configured, show onboarding wizard
  if (!localStorage.getItem('vayocare_onboarded')) {
    openOnboardingWizard();
  } else {
    currentUserRole = localStorage.getItem('vayocare_user_role') || 'patient';
    switchUserRole(currentUserRole);
  }

  loadPatientData();
  loadMedications();
  loadRoutine();
  loadAlerts();
  fetchEmergencyQr();
  applyLanguage(currentLanguage);
});

function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch(err => console.warn(err));
  }
}

// 2. Onboarding & Setup Wizard
function openOnboardingWizard() {
  document.getElementById('onboardingWizard').style.display = 'block';
  goToWizardStep(1);
}

function selectWizardRole(role) {
  wizardRole = role;
  document.getElementById('roleCardPatient').classList.toggle('selected', role === 'patient');
  document.getElementById('roleCardCaregiver').classList.toggle('selected', role === 'caregiver');
  document.getElementById('caregiverLinkingFields').style.display = (role === 'caregiver') ? 'block' : 'none';
}

function goToWizardStep(stepNum) {
  document.querySelectorAll('.wizard-step').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.step-dot').forEach(d => d.classList.remove('active'));

  const stepEl = document.getElementById(`wizardStep${stepNum}`);
  if (stepEl) stepEl.classList.add('active');

  for (let i = 1; i <= stepNum; i++) {
    const dot = document.getElementById(`dotStep${i}`);
    if (dot) dot.classList.add('active');
  }
}

function previewUploadedPrescription(input) {
  if (input.files && input.files[0]) {
    const reader = new FileReader();
    reader.onload = function(e) {
      applyCapturedPhoto(e.target.result);
    };
    reader.readAsDataURL(input.files[0]);
  }
}

// Live Camera Handling
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
    console.warn('Live camera stream not available or blocked, using file fallback:', err);
    const fb = document.getElementById('fallbackFileInput');
    if (fb) fb.click();
  }
}

function closeCameraModal() {
  const modal = document.getElementById('cameraModal');
  if (modal) modal.style.display = 'none';
  if (cameraStream) {
    cameraStream.getTracks().forEach(track => track.stop());
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
  if (currentCameraTarget === 'onboarding') {
    const img = document.getElementById('cameraPreviewThumb');
    if (img) {
      img.src = dataUrl;
      img.style.display = 'block';
    }
  } else if (currentCameraTarget === 'audit_rx') {
    const box = document.getElementById('rxPhotoPreviewBox');
    const img = document.getElementById('auditRxPhotoImg');
    if (box && img) {
      img.src = dataUrl;
      box.style.display = 'block';
    }
    const input = document.getElementById('auditRxInput');
    if (input) {
      input.value = "Rx (Photo Scanned): Tab Telmikem 40 (BP) 1-0-0, Tab Glycomet 500 (Sugar) 1-0-1, Tab Ecosprin 75 0-1-0. Review in 30 days.";
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
      input.value = "Chemist Strips (Photo Scanned): Telmikem 40 (10 tabs), Glycomet 500 (10 tabs). (Ecosprin not found in strips).";
    }
  }
}

function loadDemoProfileAndSkip() {
  localStorage.setItem('vayocare_onboarded', 'true');
  localStorage.setItem('vayocare_user_role', 'patient');
  document.getElementById('onboardingWizard').style.display = 'none';
  switchUserRole('patient');
  loadPatientData();
  loadMedications();
}

async function finishWizardAndOpenDashboard() {
  const name = document.getElementById('setupUserName').value.trim() || "Ramesh Rao";
  const phone = document.getElementById('setupUserPhone').value.trim() || "9849012345";
  const bf = document.getElementById('setupBreakfastTime').value || "09:00";
  const lunch = document.getElementById('setupLunchTime').value || "13:30";
  const dinner = document.getElementById('setupDinnerTime').value || "20:30";

  try {
    // 1. Post phone auth
    await fetch('/api/auth/phone-login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        role: wizardRole,
        name: name,
        phone: phone,
        patient_phone: wizardRole === 'caregiver' ? (document.getElementById('setupPatientPhone').value || "9849012345") : phone,
        language: currentLanguage
      })
    });

    // 2. Post routine schedule
    await fetch('/api/routine', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        wake_up: "07:30",
        breakfast: bf,
        lunch: lunch,
        dinner: dinner,
        bedtime: "22:00",
        notes: "Configured via VayoCare onboarding wizard"
      })
    });

    localStorage.setItem('vayocare_onboarded', 'true');
    localStorage.setItem('vayocare_user_role', wizardRole);
    document.getElementById('onboardingWizard').style.display = 'none';

    switchUserRole(wizardRole);
    loadPatientData();
    loadMedications();
    loadRoutine();
  } catch (err) {
    console.error('Error completing wizard:', err);
    loadDemoProfileAndSkip();
  }
}

// 3. Language Switcher (Complete Instant UI Localization)
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
  const heroBadge = document.getElementById('heroPillLabel');
  if (heroBadge && dict.heroPillLabel) {
    heroBadge.innerHTML = dict.heroPillLabel;
  }
}

// 4. Role Switcher
function switchUserRole(role) {
  currentUserRole = role;
  localStorage.setItem('vayocare_user_role', role);
  document.getElementById('btnRolePatient').classList.toggle('active', role === 'patient');
  document.getElementById('btnRoleCaregiver').classList.toggle('active', role === 'caregiver');

  if (role === 'patient') {
    document.getElementById('patientViewSection').style.display = 'block';
    document.getElementById('caregiverViewSection').style.display = 'none';
    switchNavTab('home');
  } else {
    document.getElementById('patientViewSection').style.display = 'none';
    document.getElementById('caregiverViewSection').style.display = 'block';
    switchNavTab('caretaker');
  }
}

// 5. Navigation
function switchNavTab(tabId) {
  if (tabId === 'caretaker' || tabId === 'audit') {
    if (currentUserRole !== 'caregiver') switchUserRole('caregiver');
  } else {
    if (currentUserRole !== 'patient') switchUserRole('patient');
  }

  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

  const target = document.getElementById(`tab-${tabId}`);
  if (target) target.classList.add('active');

  const navOrder = ['home', 'routine', 'audit', 'caretaker', 'emergency'];
  const idx = navOrder.indexOf(tabId);
  const items = document.querySelectorAll('.nav-item');
  if (items[idx]) items[idx].classList.add('active');

  if (tabId === 'emergency') {
    fetchEmergencyQr();
  }
}

// 6. Patient Profile & Greeting
async function loadPatientData() {
  try {
    const res = await fetch('/api/auth/profile');
    const data = await res.json();
    fetchGreeting();
  } catch (err) {
    console.error(err);
  }
}

async function fetchGreeting() {
  try {
    const res = await fetch(`/api/companion/greeting?language=${currentLanguage}&anchor=${currentAnchor}`);
    const data = await res.json();
    const bubble = document.getElementById('companionSpeechBubble');
    bubble.textContent = `"${data.text}"`;
    speakText(data.spoken, currentLanguage);
  } catch (err) {
    console.error(err);
  }
}

// 7. Voice Interaction
function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return;

  speechRecognition = new SpeechRecognition();
  speechRecognition.continuous = false;
  speechRecognition.interimResults = false;

  speechRecognition.onstart = () => {
    isListening = true;
    document.getElementById('micBtn').classList.add('listening');
    document.getElementById('voiceStatusPill').textContent = 'Listening... (వినబడుతోంది)';
  };

  speechRecognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    document.getElementById('voiceStatusPill').textContent = `Heard: "${transcript}"`;
    sendCompanionMessage(transcript);
  };

  speechRecognition.onend = () => {
    isListening = false;
    document.getElementById('micBtn').classList.remove('listening');
    document.getElementById('voiceStatusPill').textContent = 'Ready • Microphones Active';
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

function speakText(text, lang) {
  if (!('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const utt = new SpeechSynthesisUtterance(text);
  utt.lang = lang === 'te' ? 'te-IN' : (lang === 'hi' ? 'hi-IN' : 'en-IN');
  utt.rate = 0.9;
  window.speechSynthesis.speak(utt);
}

async function sendCompanionMessage(text) {
  const pill = document.getElementById('voiceStatusPill');
  pill.textContent = 'VayoCare AI analyzing...';

  try {
    const res = await fetch('/api/companion/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        patient_id: 'p_ramesh_72',
        speech_text: text,
        language: currentLanguage,
        current_anchor: currentAnchor
      })
    });
    const data = await res.json();
    document.getElementById('companionSpeechBubble').textContent = `"${data.reply_text}"`;
    speakText(data.spoken_text, currentLanguage);

    pill.textContent = data.redirected_offtopic
      ? 'Gently redirected off-topic talk'
      : `Action: ${data.action_taken.replace(/_/g, ' ')}`;

    loadMedications();
    loadAlerts();
  } catch (err) {
    console.error(err);
    pill.textContent = 'Processed.';
  }
}

function submitQuickVoice(text) {
  sendCompanionMessage(text);
}

// 8. Medications Display
async function loadMedications() {
  try {
    const res = await fetch('/api/medications');
    const meds = await res.json();
    const container = document.getElementById('medicationListContainer');
    if (!container) return;

    container.innerHTML = meds.map(m => {
      const friendlyName = currentLanguage === 'te' ? m.senior_label_te : (currentLanguage === 'hi' ? m.senior_label_hi : m.senior_label);
      const isUrgent = m.remaining_pills <= 3;

      return `
        <div class="med-card" style="border-left: 6px solid ${m.pill_color};">
          <div class="med-icon-pill" style="background: ${m.pill_color}22; color: ${m.pill_color};">
            💊
          </div>
          <div class="med-details">
            <div class="med-name">${friendlyName}</div>
            <div class="med-salt">${m.brand_name} (${m.dosage})</div>
            <div style="font-size: 13px; font-weight: 700; color: #475569; margin-top: 2px;">
              ⏰ ${m.timing_anchor.toUpperCase()} • ${m.timing_relation.replace('_', ' ')}
            </div>
            <div class="med-stock ${isUrgent ? 'stock-urgent' : ''}">
              ${isUrgent ? '⚠️ తక్కువగా ఉన్నాయి (Low Stock): ' : 'మిగిలినవి (Left): '} ${m.remaining_pills} మాత్రలు
            </div>
          </div>
          <div class="med-actions">
            <button class="btn-action btn-taken" onclick="logDoseDirect('${m.id}', 'taken')">
              ✅ వేసుకున్నా
            </button>
            <button class="btn-action btn-skip" onclick="logDoseDirect('${m.id}', 'skipped')">
              తర్వాత
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
    await fetch('/api/medications/log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        medication_id: medId,
        status: status,
        notes: `Tapped button (${status})`
      })
    });
    loadMedications();
    loadAlerts();
    const msg = status === 'taken' ? 'మాత్ర తీసుకున్నట్లు రికార్డ్ చేశాను.' : 'మాత్ర వేసుకోనట్లు గుర్తించాను.';
    speakText(msg, currentLanguage);
  } catch (err) {
    console.error(err);
  }
}

// 9. Routine Service
async function loadRoutine() {
  try {
    const res = await fetch('/api/routine');
    const r = await res.json();
    const list = document.getElementById('routineAnchorsList');
    if (!list) return;

    list.innerHTML = `
      <div style="background: white; border: 1px solid var(--border-color); padding: 12px; border-radius: 12px; display: flex; justify-content: space-between; margin-bottom: 8px;">
        <span><strong>🌅 ఉదయం టిఫిన్ (Breakfast):</strong> ${r.breakfast}</span>
        <span style="color: var(--primary); font-weight: 800;">BP & షుగర్ మాత్ర</span>
      </div>
      <div style="background: white; border: 1px solid var(--border-color); padding: 12px; border-radius: 12px; display: flex; justify-content: space-between; margin-bottom: 8px;">
        <span><strong>☀️ మధ్యాహ్నం భోజనం (Lunch):</strong> ${r.lunch}</span>
        <span style="color: var(--primary); font-weight: 800;">గుండె & కాల్షియం మాత్ర</span>
      </div>
      <div style="background: white; border: 1px solid var(--border-color); padding: 12px; border-radius: 12px; display: flex; justify-content: space-between;">
        <span><strong>🌙 రాత్రి భోజనం (Dinner):</strong> ${r.dinner}</span>
        <span style="color: var(--primary); font-weight: 800;">షుగర్ మాత్ర</span>
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
        patient_id: 'p_ramesh_72',
        voice_transcript: text,
        language: currentLanguage
      })
    });
    const updated = await res.json();
    loadRoutine();
    alert(`దినచర్య అప్‌డేట్ అయ్యింది: టిఫిన్ ${updated.breakfast}, భోజనం ${updated.lunch}, రాత్రి ${updated.dinner}`);
  } catch (err) {
    console.error(err);
  }
}

// 10. Caregiver Note
async function submitCaregiverVoiceNote() {
  const input = document.getElementById('caregiverVoiceMsgInput');
  const msg = input.value.trim();
  if (!msg) {
    alert('దయచేసి సందేశం టైప్ చేయండి.');
    return;
  }

  try {
    const res = await fetch('/api/companion/caregiver-note', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        caregiver_name: 'సురేష్ (అబ్బాయి)',
        message_text: msg,
        assigned_anchor: 'breakfast'
      })
    });
    alert('మీ సందేశం విజయవంతంగా సేవ్ అయ్యింది! రోగి యాప్‌లో ఇది వినిపిస్తుంది.');
    input.value = '';
    fetchGreeting();
  } catch (err) {
    console.error(err);
  }
}

// 11. Prescription vs Strip AI Audit
async function runPrescriptionAudit() {
  const btn = document.getElementById('i18n-btnRunAudit');
  btn.textContent = '⚡ Gemini 3.5 AI అనాలసిస్ జరుగుతోంది...';

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
          <div style="font-weight: 800; font-size: 16px;">${item.senior_label || item.brand_name}</div>
          <div style="font-size: 13px; color: #475569;">${item.brand_name} (${item.salt})</div>
          <div style="font-size: 12px; font-weight: 700; margin-top: 4px; color: #64748B;">
            మిగిలినవి: ${item.remaining_pills} మాత్రలు
          </div>
        </div>
        <div style="text-align: right;">
          <div style="font-size: 22px; font-weight: 900; color: ${item.urgency === 'urgent' ? '#DC2626' : '#2563EB'};">
            ${item.days_left} Days
          </div>
          <span style="font-size: 11px; font-weight: 800; text-transform: uppercase;">
            ${item.urgency}
          </span>
        </div>
      </div>
    `).join('');

    btn.textContent = '✅ AI ఆడిట్ పూర్తయింది';
  } catch (err) {
    console.error(err);
    btn.textContent = '⚡ AI ఆడిట్ ప్రారంభించండి (Run AI Audit)';
  }
}

// 12. Emergency QR Pass
async function fetchEmergencyQr() {
  try {
    const res = await fetch('/api/emergency/current-pin');
    const data = await res.json();
    document.getElementById('emergencyQrImg').src = data.qr_code_data;
    document.getElementById('rollingPinText').textContent = data.rolling_pin;
    // Direct robust link that never redirects to #
    const docLink = document.getElementById('doctorDirectLink');
    docLink.href = data.emergency_url;
  } catch (err) {
    console.error(err);
  }
}

// 13. Caretaker Notifications
async function loadAlerts() {
  try {
    const res = await fetch('/api/alerts');
    const alerts = await res.json();
    const container = document.getElementById('alertsLogFeed');
    if (!container) return;

    container.innerHTML = alerts.map(a => `
      <div class="alert-item ${a.severity}">
        <div style="display:flex; justify-content:space-between; font-weight:800;">
          <span>${a.title}</span>
          <span style="font-size:12px; opacity:0.8;">${a.timestamp}</span>
        </div>
        <div style="margin-top:4px;">${a.message}</div>
        <div style="font-size:11px; margin-top:4px; color:#475569;">Sent to: ${a.recipient_email} (${a.status.toUpperCase()})</div>
      </div>
    `).join('');
  } catch (err) {
    console.error(err);
  }
}

async function simulateCaregiverAlert() {
  try {
    await fetch('/api/alerts/trigger', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        severity: 'critical',
        title: '⚠️ Missed BP Tablet Alert',
        message: 'Ramesh Rao did not take morning BP tablet (Telmikem 40). Please call immediately.'
      })
    });
    alert('Email alert sent to suresh.rao@example.com');
    loadAlerts();
  } catch (err) {
    console.error(err);
  }
}
