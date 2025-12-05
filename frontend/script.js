const API_BASE = "http://localhost:8000/api";

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
      `Companion · Mood: ${data.mood} · Sentiment: ${data.sentiment_score.toFixed(
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
      "Companion"
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
Companion: ${data.reply}`;
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






