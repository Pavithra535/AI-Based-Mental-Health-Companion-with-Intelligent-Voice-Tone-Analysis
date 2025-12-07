const API_BASE = "http://localhost:8000/api";

// Page elements
const landingPage = document.getElementById("landing-page");
const welcomePage = document.getElementById("welcome-page");
const chatbotPage = document.getElementById("chatbot-page");
const beginJourneyBtn = document.getElementById("begin-journey-btn");
const startTherapyBtn = document.getElementById("start-therapy-btn");

// Activity elements
const breathingBtn = document.getElementById("breathing-btn");
const breathingCircle = document.getElementById("breathing-circle");
const breathingText = document.getElementById("breathing-text");
const breathingCount = document.getElementById("breathing-count");
const soundButtons = document.querySelectorAll(".sound-btn");
const soundVolume = document.getElementById("sound-volume");
const volumeValue = document.getElementById("volume-value");

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

// Audio context for nature sounds
let audioContext = null;
let currentSound = null;
let isBreathingActive = false;
let breathingInterval = null;

// Navigation: Show welcome page when "Begin Journey" is clicked
beginJourneyBtn.addEventListener("click", () => {
  landingPage.style.display = "none";
  welcomePage.style.display = "block";
});

// Navigation: Show chatbot page when "Start Therapy" is clicked
startTherapyBtn.addEventListener("click", () => {
  welcomePage.style.display = "none";
  chatbotPage.style.display = "block";
  // Stop any active sounds
  stopAllSounds();
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
    breathingCircle.className = "breathing-circle breathing-inhale";
    
    setTimeout(() => {
      if (!isBreathingActive) return;
      
      // Hold
      breathingText.textContent = "Hold...";
      breathingCircle.className = "breathing-circle breathing-hold";
      
      setTimeout(() => {
        if (!isBreathingActive) return;
        
        // Exhale
        breathingText.textContent = "Breathe Out...";
        breathingCircle.className = "breathing-circle breathing-exhale";
        
        setTimeout(() => {
          if (!isBreathingActive) return;
          
          // Pause
          breathingText.textContent = "Pause...";
          breathingCircle.className = "breathing-circle breathing-pause";
          
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
  breathingCircle.className = "breathing-circle";
  if (breathingInterval) {
    clearInterval(breathingInterval);
    breathingInterval = null;
  }
}

// Nature Sounds
soundButtons.forEach(btn => {
  btn.addEventListener("click", () => {
    const soundType = btn.dataset.sound;
    
    // Toggle active state
    if (btn.classList.contains("active")) {
      stopSound();
      btn.classList.remove("active");
    } else {
      // Remove active from all buttons
      soundButtons.forEach(b => b.classList.remove("active"));
      // Start new sound
      startSound(soundType);
      btn.classList.add("active");
    }
  });
});

// Volume control
soundVolume.addEventListener("input", (e) => {
  const volume = e.target.value;
  volumeValue.textContent = volume;
  if (currentSound && currentSound.gainNode) {
    currentSound.gainNode.gain.value = volume / 100;
  }
});

function startSound(type) {
  stopSound(); // Stop any existing sound
  
  if (!audioContext) {
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
  }
  
  const masterGain = audioContext.createGain();
  masterGain.connect(audioContext.destination);
  masterGain.gain.value = soundVolume.value / 100;
  
  const components = [];
  let variationInterval;
  
  switch(type) {
    case "forest":
      // Forest: Wind through trees (low rumble) + rustling leaves (mid-high noise)
      const forestWind = createNoiseGenerator(audioContext, 0.15, 50, 200);
      const forestRustle = createNoiseGenerator(audioContext, 0.2, 500, 2000);
      const forestLow = createOscillator(audioContext, 80, "sine", 0.1, masterGain);
      
      forestWind.connect(masterGain);
      forestRustle.connect(masterGain);
      forestLow.connect(masterGain);
      
      components.push(forestWind, forestRustle, forestLow);
      
      // Add occasional bird-like chirps
      variationInterval = setInterval(() => {
        if (Math.random() > 0.7) {
          const chirp = createOscillator(audioContext, 800 + Math.random() * 400, "sine", 0.15, masterGain);
          chirp.start();
          chirp.stop(audioContext.currentTime + 0.3);
        }
      }, 2000);
      break;
      
    case "ocean":
      // Ocean: Deep wave rumble + white noise for foam + periodic wave crashes
      const oceanRumble = createOscillator(audioContext, 40, "sine", 0.3, masterGain);
      const oceanNoise = createNoiseGenerator(audioContext, 0.25, 100, 800);
      const oceanMid = createOscillator(audioContext, 60, "sine", 0.2, masterGain);
      
      oceanRumble.connect(masterGain);
      oceanNoise.connect(masterGain);
      oceanMid.connect(masterGain);
      
      components.push(oceanRumble, oceanNoise, oceanMid);
      
      // Wave crash effect
      variationInterval = setInterval(() => {
        const crash = createNoiseGenerator(audioContext, 0.4, 200, 3000);
        crash.connect(masterGain);
        setTimeout(() => {
          if (crash.stop) crash.stop();
        }, 800);
      }, 4000);
      break;
      
    case "rain":
      // Rain: High-frequency white noise with variation
      const rainMain = createNoiseGenerator(audioContext, 0.3, 2000, 8000);
      const rainDrops = createNoiseGenerator(audioContext, 0.2, 5000, 12000);
      const rainAmbient = createNoiseGenerator(audioContext, 0.15, 1000, 4000);
      
      rainMain.connect(masterGain);
      rainDrops.connect(masterGain);
      rainAmbient.connect(masterGain);
      
      components.push(rainMain, rainDrops, rainAmbient);
      break;
      
    case "birds":
      // Birds: Multiple oscillators with varying frequencies and timing
      const bird1 = createOscillator(audioContext, 1200, "sine", 0.2, masterGain);
      const bird2 = createOscillator(audioContext, 1500, "sine", 0.15, masterGain);
      const bird3 = createOscillator(audioContext, 1800, "sine", 0.18, masterGain);
      
      bird1.connect(masterGain);
      bird2.connect(masterGain);
      bird3.connect(masterGain);
      
      components.push(bird1, bird2, bird3);
      
      // Vary bird frequencies to create chirping effect
      variationInterval = setInterval(() => {
        if (bird1 && bird1.frequency) {
          bird1.frequency.setValueAtTime(1000 + Math.random() * 600, audioContext.currentTime);
        }
        if (bird2 && bird2.frequency) {
          bird2.frequency.setValueAtTime(1300 + Math.random() * 500, audioContext.currentTime);
        }
        if (bird3 && bird3.frequency) {
          bird3.frequency.setValueAtTime(1600 + Math.random() * 400, audioContext.currentTime);
        }
      }, 500);
      
      // Add occasional chirps
      const chirpInterval = setInterval(() => {
        if (Math.random() > 0.5) {
          const chirp = createOscillator(audioContext, 2000 + Math.random() * 1000, "sine", 0.25, masterGain);
          chirp.start();
          chirp.stop(audioContext.currentTime + 0.2 + Math.random() * 0.3);
        }
      }, 1500);
      if (variationInterval) {
        components.push({ stop: () => clearInterval(chirpInterval) });
      }
      break;
  }
  
  currentSound = { 
    gainNode: masterGain, 
    components: components.filter(Boolean),
    variationInterval 
  };
}

function createOscillator(audioContext, freq, type, volume, output) {
  const osc = audioContext.createOscillator();
  const gain = audioContext.createGain();
  osc.type = type;
  osc.frequency.value = freq;
  gain.gain.value = volume;
  osc.connect(gain);
  gain.connect(output);
  osc.start();
  return osc;
}

function createNoiseGenerator(audioContext, volume, lowFreq, highFreq) {
  const bufferSize = audioContext.sampleRate * 2;
  const buffer = audioContext.createBuffer(1, bufferSize, audioContext.sampleRate);
  const data = buffer.getChannelData(0);
  
  for (let i = 0; i < bufferSize; i++) {
    data[i] = Math.random() * 2 - 1;
  }
  
  const noise = audioContext.createBufferSource();
  noise.buffer = buffer;
  noise.loop = true;
  
  // Filter to shape the noise
  const filter = audioContext.createBiquadFilter();
  filter.type = "bandpass";
  filter.frequency.value = (lowFreq + highFreq) / 2;
  filter.Q.value = 1;
  
  const gain = audioContext.createGain();
  gain.gain.value = volume;
  
  noise.connect(filter);
  filter.connect(gain);
  
  noise.start();
  
  return {
    connect: (destination) => gain.connect(destination),
    stop: () => {
      noise.stop();
      if (filter.disconnect) filter.disconnect();
      if (gain.disconnect) gain.disconnect();
    }
  };
}

function stopSound() {
  if (currentSound) {
    currentSound.components.forEach(component => {
      if (component && component.stop) {
        component.stop();
      } else if (component && component.disconnect) {
        component.disconnect();
      }
    });
    if (currentSound.variationInterval) {
      clearInterval(currentSound.variationInterval);
    }
    if (currentSound.gainNode) {
      currentSound.gainNode.disconnect();
    }
    currentSound = null;
  }
}

function stopAllSounds() {
  stopSound();
  stopBreathing();
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






