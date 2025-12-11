const API_BASE = "http://localhost:8000/api";

// Page elements
const landingPage = document.getElementById("landing-page");
const welcomePage = document.getElementById("welcome-page");
const chatbotPage = document.getElementById("chatbot-page");
const beginJourneyBtn = document.getElementById("begin-journey-btn");
const startTherapyBtn = document.getElementById("start-therapy-btn");

// Activity elements
const breathingBtn = document.getElementById("breathing-btn");
const breathingWaves = document.getElementById("breathing-waves");
const breathingText = document.getElementById("breathing-text");
const breathingCount = document.getElementById("breathing-count");
const meditationTimer = document.getElementById("meditation-timer");
const meditationStartBtn = document.getElementById("meditation-start-btn");
const meditationResetBtn = document.getElementById("meditation-reset-btn");
const timerButtons = document.querySelectorAll(".timer-btn");
const gratitudeInput = document.getElementById("gratitude-input");
const gratitudeAddBtn = document.getElementById("gratitude-add-btn");
const gratitudeList = document.getElementById("gratitude-list");
const relaxationStartBtn = document.getElementById("relaxation-start-btn");
const relaxationSteps = document.getElementById("relaxation-steps");

// Chat elements
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatLog = document.getElementById("chat-log");
const recordBtn = document.getElementById("record-btn");
const recordStatus = document.getElementById("record-status");
const voiceResult = document.getElementById("voice-result");

const chatSection = document.getElementById("chat-section");
const voiceSection = document.getElementById("voice-section");

let mediaRecorder = null;
let audioChunks = [];
// Track conversation history for context awareness
let conversationHistory = [];

let isBreathingActive = false;
let breathingInterval = null;
let meditationInterval = null;
let meditationTimeLeft = 0;
let relaxationActive = false;
let currentRelaxationStep = 0;

// Navigation: Show welcome page when "Begin Journey" is clicked
beginJourneyBtn.addEventListener("click", () => {
  landingPage.style.display = "none";
  welcomePage.style.display = "block";
});

// Navigation: Show chatbot page when "Start Therapy" is clicked
startTherapyBtn.addEventListener("click", () => {
  welcomePage.style.display = "none";
  chatbotPage.style.display = "block";
  // Stop any active activities
  stopBreathing();
  stopMeditation();
  stopRelaxation();
  // Focus on chat input when page loads
  setTimeout(() => {
    chatInput.focus();
  }, 100);
});

// Breathing Exercise
breathingBtn.addEventListener("click", () => {
  if (isBreathingActive) {
    stopBreathing();
  } else {
    startBreathing();
  }
});

function startBreathing() {
  isBreathingActive = true;
  breathingBtn.textContent = "Stop Breathing";
  let cycle = 0;
  
  function breathingCycle() {
    if (!isBreathingActive) return;
    
    cycle++;
    breathingCount.textContent = `Cycle ${cycle}`;
    
    // Inhale
    breathingText.textContent = "Breathe In...";
    breathingWaves.className = "breathing-waves breathing-inhale";
    
    setTimeout(() => {
      if (!isBreathingActive) return;
      
      // Hold
      breathingText.textContent = "Hold...";
      breathingWaves.className = "breathing-waves breathing-hold";
      
      setTimeout(() => {
        if (!isBreathingActive) return;
        
        // Exhale
        breathingText.textContent = "Breathe Out...";
        breathingWaves.className = "breathing-waves breathing-exhale";
        
        setTimeout(() => {
          if (!isBreathingActive) return;
          
          // Pause
          breathingText.textContent = "Pause...";
          breathingWaves.className = "breathing-waves";
          
          setTimeout(() => {
            if (!isBreathingActive) return;
            breathingCycle();
          }, 2000);
        }, 4000);
      }, 4000);
    }, 4000);
  }
  
  breathingCycle();
}

function stopBreathing() {
  isBreathingActive = false;
  breathingBtn.textContent = "Start Breathing";
  breathingText.textContent = "Click Start to begin";
  breathingCount.textContent = "";
  breathingWaves.className = "breathing-waves";
  if (breathingInterval) {
    clearInterval(breathingInterval);
    breathingInterval = null;
  }
}

// Meditation Timer
timerButtons.forEach(btn => {
  btn.addEventListener("click", () => {
    const minutes = parseInt(btn.dataset.time);
    meditationTimeLeft = minutes * 60;
    updateMeditationTimer();
    meditationResetBtn.style.display = "block";
  });
});

meditationStartBtn.addEventListener("click", () => {
  if (meditationInterval) {
    stopMeditation();
  } else {
    startMeditation();
  }
});

meditationResetBtn.addEventListener("click", () => {
  stopMeditation();
  meditationTimeLeft = 0;
  updateMeditationTimer();
  meditationResetBtn.style.display = "none";
});

function startMeditation() {
  if (meditationTimeLeft === 0) {
    alert("Please select a duration first");
    return;
  }
  meditationStartBtn.textContent = "Pause";
  meditationInterval = setInterval(() => {
    if (meditationTimeLeft > 0) {
      meditationTimeLeft--;
      updateMeditationTimer();
    } else {
      stopMeditation();
      alert("Meditation session complete! 🧘");
    }
  }, 1000);
}

function stopMeditation() {
  if (meditationInterval) {
    clearInterval(meditationInterval);
    meditationInterval = null;
  }
  meditationStartBtn.textContent = "Start";
}

function updateMeditationTimer() {
  const minutes = Math.floor(meditationTimeLeft / 60);
  const seconds = meditationTimeLeft % 60;
  meditationTimer.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

// Gratitude Journal
let gratitudeEntries = JSON.parse(localStorage.getItem('gratitudeEntries') || '[]');
renderGratitudeList();

gratitudeAddBtn.addEventListener("click", () => {
  const text = gratitudeInput.value.trim();
  if (text) {
    gratitudeEntries.push({
      text: text,
      date: new Date().toLocaleDateString()
    });
    localStorage.setItem('gratitudeEntries', JSON.stringify(gratitudeEntries));
    gratitudeInput.value = "";
    renderGratitudeList();
  }
});

gratitudeInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    gratitudeAddBtn.click();
  }
});

function renderGratitudeList() {
  gratitudeList.innerHTML = "";
  const recentEntries = gratitudeEntries.slice(-5).reverse();
  recentEntries.forEach((entry, index) => {
    const item = document.createElement("div");
    item.className = "gratitude-item";
    
    const textDiv = document.createElement("div");
    textDiv.className = "gratitude-item-text";
    textDiv.textContent = entry.text;
    
    const deleteBtn = document.createElement("button");
    deleteBtn.className = "gratitude-delete-btn";
    deleteBtn.innerHTML = "×";
    deleteBtn.title = "Delete entry";
    deleteBtn.addEventListener("click", () => {
      // Find the original index (since we reversed the array)
      const originalIndex = gratitudeEntries.length - 1 - index;
      gratitudeEntries.splice(originalIndex, 1);
      localStorage.setItem('gratitudeEntries', JSON.stringify(gratitudeEntries));
      renderGratitudeList();
    });
    
    item.appendChild(textDiv);
    item.appendChild(deleteBtn);
    gratitudeList.appendChild(item);
  });
  if (gratitudeEntries.length === 0) {
    gratitudeList.innerHTML = '<div style="color: #949fc5; font-style: italic; text-align: center; padding: 20px;">No entries yet. Start by adding something you\'re grateful for!</div>';
  }
}

// Progressive Muscle Relaxation
const relaxationStepsList = [
  "Tense your feet for 5 seconds, then release",
  "Tense your calves and thighs for 5 seconds, then release",
  "Tense your hands and arms for 5 seconds, then release",
  "Tense your shoulders and neck for 5 seconds, then release",
  "Tense your face and jaw for 5 seconds, then release",
  "Take a deep breath and relax completely"
];

function renderRelaxationSteps() {
  relaxationSteps.innerHTML = "";
  relaxationStepsList.forEach((step, index) => {
    const stepDiv = document.createElement("div");
    stepDiv.className = "relaxation-step";
    stepDiv.id = `relaxation-step-${index}`;
    stepDiv.innerHTML = `<span class="relaxation-step-number">${index + 1}.</span>${step}`;
    relaxationSteps.appendChild(stepDiv);
  });
}

renderRelaxationSteps();

relaxationStartBtn.addEventListener("click", () => {
  if (relaxationActive) {
    stopRelaxation();
  } else {
    startRelaxation();
  }
});

function startRelaxation() {
  relaxationActive = true;
  currentRelaxationStep = 0;
  relaxationStartBtn.textContent = "Stop Exercise";
  runRelaxationStep();
}

function stopRelaxation() {
  relaxationActive = false;
  relaxationStartBtn.textContent = "Start Exercise";
  document.querySelectorAll(".relaxation-step").forEach(step => {
    step.classList.remove("active");
  });
  currentRelaxationStep = 0;
}

function runRelaxationStep() {
  if (!relaxationActive) return;
  
  // Remove active from all steps
  document.querySelectorAll(".relaxation-step").forEach(step => {
    step.classList.remove("active");
  });
  
  if (currentRelaxationStep < relaxationStepsList.length) {
    const currentStepEl = document.getElementById(`relaxation-step-${currentRelaxationStep}`);
    if (currentStepEl) {
      currentStepEl.classList.add("active");
    }
    
    setTimeout(() => {
      if (!relaxationActive) return;
      currentRelaxationStep++;
      if (currentRelaxationStep < relaxationStepsList.length) {
        runRelaxationStep();
      } else {
        setTimeout(() => {
          stopRelaxation();
          alert("Relaxation exercise complete! 💆");
        }, 5000);
      }
    }, 7000); // 5 seconds tense + 2 seconds transition
  }
}

function appendMessage(role, text, meta) {
  const container = document.createElement("div");
  container.className = `message ${role}`;

  const inner = document.createElement("div");
  inner.className = "message-inner";

  if (meta) {
    const metaEl = document.createElement("div");
    metaEl.className = "meta";
    metaEl.textContent = meta;
    inner.appendChild(metaEl);
  }

  const content = document.createElement("div");
  content.textContent = text;
  inner.appendChild(content);

  container.appendChild(inner);
  chatLog.appendChild(container);
  chatLog.scrollTop = chatLog.scrollHeight;
}

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = chatInput.value.trim();
  if (!text) return;

  appendMessage("user", text, "You");
  // Add user message to conversation history
  conversationHistory.push({ role: "user", content: text });
  
  chatInput.value = "";
  chatInput.disabled = true;

  try {
    // Send conversation history for context awareness
    // Only send last 10 messages to avoid payload being too large
    const recentHistory = conversationHistory.slice(-10);
    
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ 
        message: text,
        conversation_history: recentHistory
      }),
    });

    if (!res.ok) {
      throw new Error(`Server error: ${res.status}`);
    }

    const data = await res.json();
    appendMessage(
      "bot",
      data.reply,
      `Innertone · Mood: ${data.mood} · Sentiment: ${data.sentiment_score.toFixed(
        2
      )}`
    );
    
    // Add bot response to conversation history
    conversationHistory.push({ role: "bot", content: data.reply });
    
    // Keep only last 20 messages in memory to prevent memory issues
    if (conversationHistory.length > 20) {
      conversationHistory = conversationHistory.slice(-20);
    }
  } catch (err) {
    console.error(err);
    appendMessage(
      "bot",
      "I had trouble reaching the server. Please make sure the backend is running on port 8000.",
      "Innertone"
    );
  } finally {
    chatInput.disabled = false;
    chatInput.focus();
  }
});

async function initMedia() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    alert("Your browser does not support microphone access.");
    return null;
  }
  return await navigator.mediaDevices.getUserMedia({ audio: true });
}

recordBtn.addEventListener("click", async () => {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
    return;
  }

  try {
    const stream = await initMedia();
    if (!stream) return;

    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        audioChunks.push(e.data);
      }
    };

    mediaRecorder.onstop = async () => {
      recordBtn.textContent = "Start Recording";
      recordBtn.classList.remove("recording");
      recordStatus.textContent = "Processing audio…";

      const blob = new Blob(audioChunks, { type: "audio/webm" });
      const formData = new FormData();
      formData.append("file", blob, "recording.webm");

      try {
        const res = await fetch(`${API_BASE}/analyze_voice`, {
          method: "POST",
          body: formData,
        });

        if (!res.ok) {
          throw new Error(`Server error: ${res.status}`);
        }

        const data = await res.json();
        voiceResult.textContent = `Detected mood: ${data.mood}.
Energy: ${data.energy.toFixed(4)}, Tempo: ${data.tempo.toFixed(
          1
        )} BPM.
Innertone: ${data.reply}`;
      } catch (err) {
        console.error(err);
        voiceResult.textContent =
          "I couldn't analyze the audio. Please ensure the backend is running.";
      } finally {
        recordStatus.textContent = "Idle";
        stream.getTracks().forEach((t) => t.stop());
      }
    };

    mediaRecorder.start();
    recordBtn.textContent = "Stop Recording";
    recordBtn.classList.add("recording");
    recordStatus.textContent = "Recording… speak when you’re ready.";
  } catch (err) {
    console.error(err);
    alert("Could not access microphone. Check browser permissions.");
  }
});






